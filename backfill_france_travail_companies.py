import json
import time

from database.connection import get_connection
from scrapers.france_travail import (
    build_session,
    scrape_france_travail_detail,
)


def get_jobs_missing_company():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            source_job_id,
            raw_payload
        FROM raw_jobs
        WHERE source = 'FRANCE_TRAVAIL'
          AND (
                raw_payload ->> 'company' IS NULL
                OR raw_payload ->> 'company' = ''
              )
        ORDER BY source_job_id
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def update_raw_job(job_id, raw_payload):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE raw_jobs
        SET
            raw_payload = %s::jsonb,
            scraped_at = now()
        WHERE source = 'FRANCE_TRAVAIL'
          AND source_job_id = %s
        """,
        (
            json.dumps(raw_payload),
            job_id,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()


def main():
    rows = get_jobs_missing_company()

    print(
        f"France Travail raw jobs missing company: "
        f"{len(rows)}"
    )

    if not rows:
        print("Nothing to backfill.")
        return

    session = build_session()

    success_count = 0
    failure_count = 0

    for index, (job_id, raw_payload) in enumerate(
        rows,
        start=1,
    ):
        url = raw_payload.get("url")

        print(
            f"Backfilling company "
            f"{index}/{len(rows)} - {job_id}"
        )

        if not url:
            print(
                f"WARNING: {job_id} has no URL. Skipping."
            )
            failure_count += 1
            continue

        try:
            detail_job = scrape_france_travail_detail(
                url,
                session=session,
            )

            company = detail_job.get("company")

            if not company:
                print(
                    f"WARNING: no company found "
                    f"for {job_id}"
                )
                failure_count += 1
                continue

            # Preserve the existing raw payload and only
            # add/update the company field.
            raw_payload["company"] = company

            update_raw_job(
                job_id,
                raw_payload,
            )

            success_count += 1

        except Exception as exc:
            print(
                f"WARNING: failed {job_id}: {exc}"
            )
            failure_count += 1

        time.sleep(1)

    print("\n--- BACKFILL COMPLETE ---")
    print("Successfully updated:", success_count)
    print("Failed/skipped:", failure_count)


if __name__ == "__main__":
    main()