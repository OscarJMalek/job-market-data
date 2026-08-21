import os

import psycopg2
from dotenv import load_dotenv

from transformers.france_travail import (
    transform_france_travail_job,
)


load_dotenv()

database_url = os.environ["DATABASE_URL"]

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

cursor.execute(
    """
    SELECT raw_payload
    FROM raw_jobs
    WHERE source = 'FRANCE_TRAVAIL'
    ORDER BY scraped_at DESC
    LIMIT 10
    """
)

rows = cursor.fetchall()

cursor.close()
conn.close()


for index, row in enumerate(rows, start=1):
    raw_job = row[0]

    transformed_job = transform_france_travail_job(
        raw_job
    )

    print("\n" + "=" * 80)
    print(f"JOB {index}")

    for key, value in transformed_job.items():
        if key == "description" and value:
            print(
                f"{key}: "
                f"{value[:300]}..."
            )
        else:
            print(f"{key}: {value}")