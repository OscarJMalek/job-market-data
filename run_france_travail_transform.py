import os

import psycopg2
from dotenv import load_dotenv

from database.connection import upsert_jobs
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
    """
)

raw_jobs = [
    row[0]
    for row in cursor.fetchall()
]

cursor.close()
conn.close()


print(
    f"France Travail raw jobs found: "
    f"{len(raw_jobs)}"
)


transformed_jobs = [
    transform_france_travail_job(job)
    for job in raw_jobs
]


print(
    f"France Travail jobs transformed: "
    f"{len(transformed_jobs)}"
)


upsert_jobs(transformed_jobs)