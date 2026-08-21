from scrapers.apec import scrape_apec
from transformers.apec import transform_apec_job
from database.connection import (
    upsert_raw_jobs,
    upsert_jobs,
    mark_missing_jobs_closed,
    get_apec_sector_mapping,
    get_active_jobs_by_source,
)


SOURCE = "APEC"


def main():
    # 1. Extract all current APEC jobs
    raw_jobs = scrape_apec()

    if not raw_jobs:
        raise RuntimeError(
            "APEC scrape returned no jobs. "
            "Aborting pipeline to protect lifecycle data."
        )

    # 2. Deduplicate the current scrape by APEC offer number
    unique_raw_jobs = {
        job["numeroOffre"]: job
        for job in raw_jobs
    }

    raw_jobs = list(unique_raw_jobs.values())

    print(
        f"APEC: {len(raw_jobs)} unique jobs "
        f"collected in current scrape."
    )

    # 3. Store the raw APEC payloads
    upsert_raw_jobs(
        source=SOURCE,
        jobs=raw_jobs,
        source_id_field="numeroOffre",
    )

    # 4. Load APEC sector reference data once
    sector_mapping = get_apec_sector_mapping()

    # 5. Transform the raw jobs
    transformed_jobs = [
        transform_apec_job(
            job,
            sector_mapping=sector_mapping,
        )
        for job in raw_jobs
    ]

    # 6. Store the transformed jobs
    upsert_jobs(transformed_jobs)

    # 7. Build the current active-ID set
    active_job_ids = [
        job["source_job_id"]
        for job in transformed_jobs
    ]

    # 8. Check whether the scrape looks complete enough
    #    before closing previously active jobs.
    existing_active_jobs = get_active_jobs_by_source(
        SOURCE
    )

    previous_active_count = len(existing_active_jobs)
    current_count = len(active_job_ids)

    print("\n--- APEC LIFECYCLE SAFETY CHECK ---")
    print("Previously active:", previous_active_count)
    print("Current scrape:", current_count)

    # Require the new scrape to contain at least 70% of the
    # previously active population before allowing closures.
    #
    # This protects us against silent partial API responses.
    minimum_safe_count = int(
        previous_active_count * 0.70
    )

    if (
        previous_active_count > 0
        and current_count < minimum_safe_count
    ):
        print(
            "WARNING: APEC scrape is much smaller than "
            "the previous active population."
        )
        print(
            "Closure step skipped to protect historical data."
        )

        return

    # 9. Mark genuinely missing APEC jobs as closed
    mark_missing_jobs_closed(
        source=SOURCE,
        active_job_ids=active_job_ids,
    )

    print("\nAPEC pipeline complete.")


if __name__ == "__main__":
    main()