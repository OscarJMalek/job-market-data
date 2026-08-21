import time

from database.connection import (
    get_existing_source_job_ids,
    upsert_raw_jobs,
)
from scrapers.france_travail import (
    build_session,
    scrape_france_travail_search,
    scrape_france_travail_detail,
)


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


# -------------------------
# SEARCH
# -------------------------

finance_jobs = scrape_france_travail_search(
    search_name="finance",
    search_url=FINANCE_URL,
)

comptabilite_jobs = scrape_france_travail_search(
    search_name="comptabilite",
    search_url=COMPTABILITE_URL,
)


# Deduplicate the two searches by France Travail offer ID
search_jobs = {}

for job in finance_jobs + comptabilite_jobs:
    search_jobs[job["source_job_id"]] = job


print("\nUnique search jobs:", len(search_jobs))


# -------------------------
# FIND NEW JOBS
# -------------------------

existing_ids = get_existing_source_job_ids(
    "FRANCE_TRAVAIL"
)

new_ids = sorted(
    set(search_jobs.keys()) - existing_ids
)

print("Already stored:", len(existing_ids))
print("New jobs:", len(new_ids))


# -------------------------
# TEST: FETCH ONLY 10 DETAILS
# -------------------------

test_ids = new_ids[:10]

detail_jobs = []

session = build_session()

for index, job_id in enumerate(test_ids, start=1):
    search_job = search_jobs[job_id]

    print(
        f"Fetching detail {index}/{len(test_ids)}: "
        f"{job_id}"
    )

    detail_job = scrape_france_travail_detail(
        search_job["url"],
        session=session,
    )

    detail_jobs.append(detail_job)

    time.sleep(1)


print(
    f"\nSuccessfully fetched "
    f"{len(detail_jobs)} detail records."
)


# -------------------------
# LOAD RAW DATA
# -------------------------

upsert_raw_jobs(
    source="FRANCE_TRAVAIL",
    jobs=detail_jobs,
    source_id_field="source_job_id",
)