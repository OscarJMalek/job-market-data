import os
import hashlib
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.environ["DATABASE_URL"]

print("DATABASE_URL fingerprint:", hashlib.sha256(database_url.encode()).hexdigest())

conn = psycopg2.connect(database_url)

cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO test_jobs
    (title, company, location, salary_min, salary_max, source, url)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
    (
        "Junior Financial Analyst",
        "Test Company",
        "Lyon",
        35000,
        40000,
        "Test",
        "https://example.com/test-job",
    ),
)

conn.commit()

cursor.close()
conn.close()

print("Test job successfully inserted into Supabase!")