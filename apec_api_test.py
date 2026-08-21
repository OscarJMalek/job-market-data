import os
import json

import requests
import psycopg2
from dotenv import load_dotenv


load_dotenv()


def transform_apec_job(job):
    return {
        "title": job.get("intitule"),
        "company": job.get("nomCommercial"),
        "location": job.get("lieuTexte"),
        "department": None,
        "job_type": None,
        "work_mode": None,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": "EUR",
        "description": job.get("texteOffre"),
        "source": "APEC",
        "source_job_id": job.get("numeroOffre"),
        "url": None,
        "posted_at": job.get("datePublication"),
        "status": "active",
    }


# Apec search endpoint
url = "https://www.apec.fr/cms/webservices/rechercheOffre"


# Search criteria:
# Finance jobs in Lyon
payload = {
    "activeFiltre": True,
    "fonctions": [],
    "idNomZonesDeplacement": [],
    "idsEtablissement": [],
    "lieux": ["596717"],
    "motsCles": "Finance",
    "niveauxExperience": [],
    "pagination": {
        "range": 20,
        "startIndex": 0
    },
    "pointGeolocDeReference": {
        "distance": 0
    },
    "positionNumbersExcluded": [],
    "secteursActivite": [],
    "sorts": [
        {
            "type": "SCORE",
            "direction": "DESCENDING"
        }
    ],
    "statutPoste": [],
    "typeClient": "CADRE",
    "typesContrat": [],
    "typesConvention": [
        "143684",
        "143685",
        "143686",
        "143687",
        "143706"
    ],
    "typesTeletravail": []
}


# -------------------------
# EXTRACT
# -------------------------

all_jobs = []

start_index = 0
page_size = 20

while True:
    payload["pagination"]["startIndex"] = start_index
    payload["pagination"]["range"] = page_size

    response = requests.post(url, json=payload)

    # Raise an error if Apec returns a bad HTTP status
    response.raise_for_status()

    data = response.json()

    jobs = data["resultats"]
    total_count = data["totalCount"]

    all_jobs.extend(jobs)

    print(
        f"Fetched {len(jobs)} jobs "
        f"starting at {start_index}. "
        f"Total collected: {len(all_jobs)}/{total_count}"
    )

    start_index += page_size

    if start_index >= total_count:
        break


print("\nFinished!")
print("Total jobs reported by Apec:", total_count)
print("Total jobs collected:", len(all_jobs))


# -------------------------
# DATA QUALITY CHECK
# -------------------------

unique_job_ids = {
    job["numeroOffre"]
    for job in all_jobs
}

print("Unique job IDs:", len(unique_job_ids))

if len(unique_job_ids) != len(all_jobs):
    print("WARNING: Duplicate job IDs detected!")
else:
    print("No duplicate job IDs detected.")


# -------------------------
# TRANSFORMATION TEST
# -------------------------

first_job = all_jobs[0]

clean_job = transform_apec_job(first_job)

print("\n--- CLEANED JOB ---")

for key, value in clean_job.items():
    print(f"{key}: {value}")


# -------------------------
# LOAD RAW DATA
# -------------------------

database_url = os.environ["DATABASE_URL"]

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

for job in all_jobs:
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
            "APEC",
            job["numeroOffre"],
            json.dumps(job),
        ),
    )

conn.commit()

cursor.close()
conn.close()

print(
    f"\n{len(all_jobs)} raw Apec jobs "
    f"successfully upserted into Supabase!"
)