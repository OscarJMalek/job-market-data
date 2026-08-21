import time

import requests

from database.connection import (
    get_active_jobs_by_source,
    refresh_jobs_last_seen,
)
from scrapers.france_travail import (
    build_session,
    scrape_france_travail_search,
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


# --------------------------------
# 1. GET CURRENT SEARCH UNIVERSE
# --------------------------------

finance_jobs = scrape_france_travail_search(
    search_name="finance",
    search_url=FINANCE_URL,
)

comptabilite_jobs = scrape_france_travail_search(
    search_name="comptabilite",
    search_url=COMPTABILITE_URL,
)

search_jobs = {}

for job in finance_jobs + comptabilite_jobs:
    search_jobs[job["source_job_id"]] = job

current_ids = set(search_jobs.keys())

print("\n--- CURRENT SEARCH ---")
print("Finance:", len(finance_jobs))
print("Comptabilite:", len(comptabilite_jobs))
print("Unique current IDs:", len(current_ids))


# --------------------------------
# 2. GET ACTIVE DATABASE JOBS
# --------------------------------

active_jobs = get_active_jobs_by_source(
    "FRANCE_TRAVAIL"
)

active_ids = {
    job["source_job_id"]
    for job in active_jobs
}

print("\n--- DATABASE ---")
print("Active France Travail jobs:", len(active_ids))


# --------------------------------
# 3. IDENTIFY DIFFERENCES
# --------------------------------

still_present_ids = active_ids & current_ids
missing_ids = active_ids - current_ids
new_ids = current_ids - active_ids

print("\n--- COMPARISON ---")
print("Still present:", len(still_present_ids))
print("Missing from search:", len(missing_ids))
print("New in search:", len(new_ids))


# --------------------------------
# 4. REFRESH STILL-PRESENT JOBS
# --------------------------------

refresh_jobs_last_seen(
    "FRANCE_TRAVAIL",
    still_present_ids,
)

print(
    f"\nRefreshed last_seen_at for "
    f"{len(still_present_ids)} jobs."
)


# --------------------------------
# 5. VERIFY MISSING JOBS
# --------------------------------

session = build_session()

confirmed_gone = []
still_live = []
unknown = []

missing_jobs = [
    job
    for job in active_jobs
    if job["source_job_id"] in missing_ids
]

print(
    f"\nChecking {len(missing_jobs)} "
    f"missing jobs individually..."
)

for index, job in enumerate(
    missing_jobs,
    start=1,
):
    job_id = job["source_job_id"]
    url = job["url"]

    print(
        f"Checking missing job "
        f"{index}/{len(missing_jobs)} - {job_id}"
    )

    if not url:
        unknown.append(job_id)
        continue

    try:
        response = session.get(
            url,
            timeout=60,
            allow_redirects=True,
        )

        if response.status_code in (404, 410):
            confirmed_gone.append(job_id)

        elif response.status_code == 200:
            still_live.append(job_id)

        else:
            print(
                f"WARNING: {job_id} returned "
                f"HTTP {response.status_code}"
            )
            unknown.append(job_id)

    except requests.RequestException as exc:
        print(
            f"WARNING: could not verify "
            f"{job_id}: {exc}"
        )
        unknown.append(job_id)

    time.sleep(1)


print("\n--- VERIFICATION RESULTS ---")
print("Confirmed gone:", len(confirmed_gone))
print("Still live:", len(still_live))
print("Unknown / request failure:", len(unknown))

print("\nConfirmed gone IDs:")
print(confirmed_gone)