import requests


job_id = "179199495W"

detail_page_url = (
    "https://www.apec.fr/candidat/recherche-emploi.html/emploi/"
    f"detail-offre/{job_id}"
    "?lieux=596717&motsCles=Finance&page=0&selectedIndex=0"
)

api_url = "https://www.apec.fr/cms/webservices/offre/public"

session = requests.Session()

# First visit the normal public job-detail page
page_response = requests.get(detail_page_url)

print("Detail page status:", page_response.status_code)
print("Cookies received:", len(session.cookies))


# Then request the underlying JSON using the same session
api_response = requests.get(
    api_url,
    params={"numeroOffre": job_id},
    headers={
        "Accept": "application/json, text/plain, */*",
        "Referer": detail_page_url,
    },
)

print("API status:", api_response.status_code)
print("Content type:", api_response.headers.get("content-type"))
print("Response length:", len(api_response.text))

api_response.raise_for_status()

data = api_response.json()

print("\n--- FULL APEC JOB ---")

for key, value in data.items():
    print(f"{key}: {value}")