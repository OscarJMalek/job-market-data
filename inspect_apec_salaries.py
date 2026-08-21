import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()

database_url = os.environ["DATABASE_URL"]

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

cursor.execute(
    """
    SELECT
        raw_payload ->> 'salaireTexte' AS salary_text,
        COUNT(*) AS job_count
    FROM raw_jobs
    WHERE source = 'APEC'
      AND raw_payload ->> 'salaireTexte' IS NOT NULL
    GROUP BY raw_payload ->> 'salaireTexte'
    ORDER BY job_count DESC, salary_text
    """
)

salary_values = cursor.fetchall()

cursor.close()
conn.close()

print(f"Distinct salary values: {len(salary_values)}")
print("\n--- APEC SALARY VALUES ---")

for salary_text, job_count in salary_values:
    print(f"{job_count:>3} | {salary_text}")