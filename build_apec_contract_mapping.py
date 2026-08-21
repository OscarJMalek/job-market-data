import os

import psycopg2
import requests
from dotenv import load_dotenv


load_dotenv()

database_url = os.environ["DATABASE_URL"]

reference_url = (
    "https://www.apec.fr"
    "/cms/webservices/referentielstatique/visuel"
)

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

cursor.execute(
    """
    SELECT DISTINCT
        (raw_payload ->> 'secteurActivite')::int
    FROM raw_jobs
    WHERE source = 'APEC'
      AND raw_payload ->> 'secteurActivite' IS NOT NULL
    ORDER BY 1
    """
)

sector_codes = [
    row[0]
    for row in cursor.fetchall()
]

cursor.close()
conn.close()

print(f"Sector codes found: {len(sector_codes)}")
print("\n--- SECTOR MAPPING ---")

for code in sector_codes:
    response = requests.get(
        reference_url,
        params={
            "presentationCode": "NAF_700_SERVICE_DOMAIN",
            "nomenclatureId": code,
        },
    )

    response.raise_for_status()

    data = response.json()

    print(f"{code}: {data.get('libelle')}")