from database.connection import get_existing_source_job_ids
from scrapers.france_travail import scrape_france_travail_search


FINANCE_URL = (
    "https://candidat.francetravail.fr/offres/recherche"
    "?lieux=69D"
    "&motsCles=finance"
    "&offresPartenaires=true"
    "&rayon=10"
    "&tri=0"
)

COMPTABILITE_URL = (
    "https://candidat.francetravail.fr/offres/recherche"
    "?lieux=69D"
    "&motsCles=comptabilite"
    "&offresPartenaires=true"
    "&rayon=10"
    "&tri=0"
)


finance_jobs = scrape_france_travail_search(
    search_name="finance",
    search_url=FINANCE_URL,
)

comptabilite_jobs = scrape_france_travail_search(
    search_name="comptabilite",
    search_url=COMPTABILITE_URL,
)


# Combine the two searches and deduplicate by France Travail ID.
search_jobs = {}

for job in finance_jobs + comptabilite_jobs:
    search_jobs[job["source_job_id"]] = job


print("\n--- SEARCH RESULTS ---")
print("Finance:", len(finance_jobs))
print("Comptabilite:", len(comptabilite_jobs))
print("Unique:", len(search_jobs))


# Find jobs that we have already stored.
existing_ids = get_existing_source_job_ids(
    "FRANCE_TRAVAIL"
)

new_ids = (
    set(search_jobs.keys())
    - existing_ids
)


print("\n--- DATABASE CHECK ---")
print("Already stored:", len(existing_ids))
print("New jobs requiring detail fetch:", len(new_ids))


print("\n--- FIRST 10 NEW JOBS ---")

for job_id in list(new_ids)[:10]:
    job = search_jobs[job_id]

    print(
        job_id,
        job["url"]
    )