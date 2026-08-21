import time

import requests

from database.connection import (
    get_active_jobs_by_source,
    get_existing_source_job_ids,
    mark_jobs_closed,
    refresh_jobs_last_seen,
    upsert_jobs,
    upsert_raw_jobs,
)
from scrapers.france_travail import (
    build_session,
    scrape_france_travail_detail,
    scrape_france_travail_search,
)
from transformers.france_travail import (
    transform_france_travail_job,
)


SOURCE = "FRANCE_TRAVAIL"

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


def main():
    # ==========================================================
    # 1. SCRAPE CURRENT SEARCH RESULTS
    # ==========================================================

    print("\n=== FRANCE TRAVAIL SEARCH ===")

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

    print("\n--- SEARCH RESULTS ---")
    print("Finance:", len(finance_jobs))
    print("Comptabilite:", len(comptabilite_jobs))
    print("Unique:", len(current_ids))

    # ==========================================================
    # 2. IDENTIFY NEW JOBS
    # ==========================================================

    existing_raw_ids = get_existing_source_job_ids(
        SOURCE
    )

    new_ids = current_ids - existing_raw_ids

    print("\n--- NEW JOB CHECK ---")
    print("Already stored:", len(current_ids & existing_raw_ids))
    print("New jobs:", len(new_ids))

    # ==========================================================
    # 3. FETCH DETAIL FOR NEW JOBS ONLY
    # ==========================================================

    session = build_session()

    new_raw_jobs = []

    new_search_jobs = [
        search_jobs[job_id]
        for job_id in sorted(new_ids)
    ]

    print(
        f"\nFetching detail for "
        f"{len(new_search_jobs)} new jobs..."
    )

    for index, search_job in enumerate(
        new_search_jobs,
        start=1,
    ):
        job_id = search_job["source_job_id"]
        url = search_job["url"]

        print(
            f"France Travail detail: "
            f"{index}/{len(new_search_jobs)} - {job_id}"
        )

        try:
            detail_job = scrape_france_travail_detail(
                url,
                session=session,
            )

            new_raw_jobs.append(detail_job)

        except requests.RequestException as exc:
            print(
                f"WARNING: failed to fetch "
                f"{job_id}: {exc}"
            )

        except Exception as exc:
            print(
                f"WARNING: failed to process "
                f"{job_id}: {exc}"
            )

        time.sleep(1)

    print(
        f"\nSuccessfully fetched "
        f"{len(new_raw_jobs)}/{len(new_search_jobs)} "
        f"new detail records."
    )

    # ==========================================================
    # 4. STORE RAW NEW JOBS
    # ==========================================================

    if new_raw_jobs:
        upsert_raw_jobs(
            source=SOURCE,
            jobs=new_raw_jobs,
            source_id_field="source_job_id",
        )

    # ==========================================================
    # 5. TRANSFORM + UPSERT NEW JOBS
    # ==========================================================

    transformed_jobs = [
        transform_france_travail_job(job)
        for job in new_raw_jobs
    ]

    if transformed_jobs:
        upsert_jobs(transformed_jobs)

    print(
        f"{len(transformed_jobs)} new jobs "
        f"transformed and upserted."
    )

    # ==========================================================
    # 6. GET ALL CURRENTLY ACTIVE DATABASE JOBS
    # ==========================================================

    active_jobs = get_active_jobs_by_source(
        SOURCE
    )

    active_ids = {
        job["source_job_id"]
        for job in active_jobs
    }

    print("\n--- LIFECYCLE CHECK ---")
    print(
        "Active jobs currently in database:",
        len(active_ids),
    )

    # ==========================================================
    # 7. REFRESH JOBS FOUND IN CURRENT SEARCH
    # ==========================================================

    still_present_ids = active_ids & current_ids

    refresh_jobs_last_seen(
        SOURCE,
        still_present_ids,
    )

    print(
        f"Found directly in current search: "
        f"{len(still_present_ids)}"
    )

    # ==========================================================
    # 8. FIND ACTIVE JOBS MISSING FROM SEARCH
    # ==========================================================

    missing_ids = active_ids - current_ids

    missing_jobs = [
        job
        for job in active_jobs
        if job["source_job_id"] in missing_ids
    ]

    print(
        f"Active jobs missing from search: "
        f"{len(missing_jobs)}"
    )

    # ==========================================================
    # 9. VERIFY MISSING JOBS INDIVIDUALLY
    # ==========================================================

    confirmed_gone = []
    still_live = []
    unknown = []

    for index, job in enumerate(
        missing_jobs,
        start=1,
    ):
        job_id = job["source_job_id"]
        url = job["url"]

        print(
            f"Verifying missing job "
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

    # ==========================================================
    # 10. REFRESH VERIFIED-LIVE JOBS
    # ==========================================================

    if still_live:
        refresh_jobs_last_seen(
            SOURCE,
            set(still_live),
        )

    # ==========================================================
    # 11. CLOSE CONFIRMED-DEAD JOBS
    # ==========================================================

    closed_count = mark_jobs_closed(
        SOURCE,
        confirmed_gone,
    )

    # ==========================================================
    # 12. FINAL SUMMARY
    # ==========================================================

    print("\n========================================")
    print("FRANCE TRAVAIL PIPELINE COMPLETE")
    print("========================================")

    print(
        "Unique jobs in current search:",
        len(current_ids),
    )

    print(
        "New jobs discovered:",
        len(new_ids),
    )

    print(
        "New detail records fetched:",
        len(new_raw_jobs),
    )

    print(
        "Found directly in search:",
        len(still_present_ids),
    )

    print(
        "Missing jobs verified live:",
        len(still_live),
    )

    print(
        "Jobs confirmed gone:",
        len(confirmed_gone),
    )

    print(
        "Jobs marked closed:",
        closed_count,
    )

    print(
        "Jobs left unchanged due to verification failure:",
        len(unknown),
    )


if __name__ == "__main__":
    main()