from scrapers.france_travail import scrape_france_travail_detail


urls = [
    "https://candidat.francetravail.fr/offres/recherche/detail/212RNCS",
    "https://candidat.francetravail.fr/offres/recherche/detail/212QRFR",
    "https://candidat.francetravail.fr/offres/recherche/detail/212GVYP",
    "https://candidat.francetravail.fr/offres/recherche/detail/212CKPV",
    "https://candidat.francetravail.fr/offres/recherche/detail/212BFHC",
]


for url in urls:
    job = scrape_france_travail_detail(url)

    print("\n" + "=" * 80)
    print(job["source_job_id"])
    print(job["title"])
    print("Location:", job["location"])
    print("Contract:", job["contract_text"])
    print("Working time:", job["working_time_text"])
    print("Salary:", job["salary_text"])
    print("Posted:", job["posted_at"])
    print("Description length:", len(job["description"] or ""))