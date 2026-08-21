import requests
from bs4 import BeautifulSoup


job_ids = [
    "0983169",
    "211HNBP",
    "212HMKG",
]

for job_id in job_ids:
    print("\n" + "=" * 80)
    print("JOB:", job_id)

    url = (
        "https://candidat.francetravail.fr"
        f"/offres/recherche/detail/{job_id}"
    )

    response = requests.get(url, timeout=60)

    print("Status:", response.status_code)

    if response.status_code != 200:
        continue

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    hiring_org = soup.select_one(
        '[itemprop="hiringOrganization"]'
    )

    if not hiring_org:
        print("No hiringOrganization")
        continue

    print("\n--- HIRING ORGANIZATION HTML ---")
    print(hiring_org.prettify()[:5000])