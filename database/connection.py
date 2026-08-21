import os
import json

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    database_url = os.environ["DATABASE_URL"]
    return psycopg2.connect(database_url)


def get_apec_sector_mapping():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            sector_code,
            sector_label
        FROM apec_sector_reference
        """
    )

    mapping = {
        row[0]: row[1]
        for row in cursor.fetchall()
    }

    cursor.close()
    conn.close()

    return mapping


def upsert_raw_jobs(source, jobs, source_id_field):
    conn = get_connection()
    cursor = conn.cursor()

    for job in jobs:
        cursor.execute(
            """
            INSERT INTO raw_jobs (
                source,
                source_job_id,
                raw_payload,
                scraped_at
            )
            VALUES (%s, %s, %s::jsonb, now())

            ON CONFLICT (source, source_job_id)
            DO UPDATE SET
                raw_payload = EXCLUDED.raw_payload,
                scraped_at = now()
            """,
            (
                source,
                job[source_id_field],
                json.dumps(job),
            ),
        )

    conn.commit()

    cursor.close()
    conn.close()

    print(
        f"{len(jobs)} raw jobs from {source} "
        f"successfully upserted into Supabase!"
    )


def upsert_jobs(jobs):
    conn = get_connection()
    cursor = conn.cursor()

    for job in jobs:
        cursor.execute(
            """
            INSERT INTO jobs (
                title,
                company,
                location,
                department,
                sector,
                job_type,
                work_mode,
                salary_min,
                salary_max,
                salary_text,
                salary_currency,
                description,
                source,
                source_job_id,
                url,
                posted_at,
                first_seen_at,
                last_seen_at,
                status,
                scraped_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, now(), now(),
                %s, now()
            )

            ON CONFLICT (source, source_job_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                location = EXCLUDED.location,
                department = EXCLUDED.department,
                sector = EXCLUDED.sector,
                job_type = EXCLUDED.job_type,
                work_mode = EXCLUDED.work_mode,
                salary_min = EXCLUDED.salary_min,
                salary_max = EXCLUDED.salary_max,
                salary_text = EXCLUDED.salary_text,
                salary_currency = EXCLUDED.salary_currency,
                description = EXCLUDED.description,
                url = EXCLUDED.url,
                posted_at = EXCLUDED.posted_at,
                last_seen_at = now(),
                status = EXCLUDED.status,
                scraped_at = now()
            """,
            (
                job["title"],
                job["company"],
                job["location"],
                job["department"],
                job["sector"],
                job["job_type"],
                job["work_mode"],
                job["salary_min"],
                job["salary_max"],
                job.get("salary_text"),
                job["salary_currency"],
                job["description"],
                job["source"],
                job["source_job_id"],
                job["url"],
                job["posted_at"],
                job["status"],
            ),
        )

    conn.commit()

    cursor.close()
    conn.close()

    print(
        f"{len(jobs)} transformed jobs "
        f"successfully upserted into Supabase!"
    )


def mark_missing_jobs_closed(source, active_job_ids):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET
            status = 'closed',
            scraped_at = now()
        WHERE source = %s
          AND status = 'active'
          AND NOT (source_job_id = ANY(%s))
        """,
        (
            source,
            active_job_ids,
        ),
    )

    closed_count = cursor.rowcount

    conn.commit()

    cursor.close()
    conn.close()

    print(
        f"{closed_count} previously active jobs from {source} "
        f"marked as closed."
    )

def get_existing_source_job_ids(source):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT source_job_id
        FROM raw_jobs
        WHERE source = %s
        """,
        (source,),
    )

    existing_ids = {
        row[0]
        for row in cursor.fetchall()
    }

    cursor.close()
    conn.close()

    return existing_ids

def get_active_jobs_by_source(source):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            source_job_id,
            url
        FROM jobs
        WHERE source = %s
          AND status = 'active'
        """,
        (source,),
    )

    jobs = [
        {
            "source_job_id": row[0],
            "url": row[1],
        }
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return jobs


def mark_job_closed(source, source_job_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET
            status = 'closed',
            scraped_at = now()
        WHERE source = %s
          AND source_job_id = %s
        """,
        (
            source,
            source_job_id,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()


def refresh_jobs_last_seen(source, source_job_ids):
    if not source_job_ids:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET
            last_seen_at = now(),
            status = 'active',
            scraped_at = now()
        WHERE source = %s
          AND source_job_id = ANY(%s)
        """,
        (
            source,
            list(source_job_ids),
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()

def mark_jobs_closed(source, source_job_ids):
    if not source_job_ids:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jobs
        SET
            status = 'closed',
            scraped_at = now()
        WHERE source = %s
          AND source_job_id = ANY(%s)
          AND status = 'active'
        """,
        (
            source,
            list(source_job_ids),
        ),
    )

    updated_count = cursor.rowcount

    conn.commit()

    cursor.close()
    conn.close()

    return updated_count