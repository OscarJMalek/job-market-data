import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.environ["DATABASE_URL"]

conn = psycopg2.connect(database_url)

cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO jobs (
        title,
        company,
        location,
        department,
        job_type,
        work_mode,
        salary_min,
        salary_max,
        salary_currency,
        description,
        source,
        source_job_id,
        url,
        posted_at,
        status
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """,
    (
        "Financial Analyst",
        "Example Finance Ltd",
        "Lyon",
        "Finance",
        "CDI",
        "Hybrid",
        40000,
        45000,
        "EUR",
        "Example job advertisement for testing our job-market-data pipeline. "
        "The successful candidate will work with financial analysis, Excel and Power BI.",
        "Test",
        "TEST-001",
        "https://example.com/jobs/TEST-001",
        "2026-08-19 09:00:00+02",
        "active",
    ),
)

conn.commit()

cursor.close()
conn.close()

print("Test job successfully inserted into jobs!")