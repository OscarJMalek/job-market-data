from playwright.sync_api import sync_playwright


job_id = "179199495W"

detail_url = (
    "https://www.apec.fr/candidat/recherche-emploi.html/emploi/"
    f"detail-offre/{job_id}"
    "?lieux=596717&motsCles=Finance&page=0&selectedIndex=0"
)

api_fragment = "/cms/webservices/offre/public"


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    detail_data = None

    def handle_response(response):
        global detail_data

        if api_fragment in response.url:
            print("Found detail API response")
            print("Status:", response.status)
            print("URL:", response.url)

            if response.status == 200:
                detail_data = response.json()

    page.on("response", handle_response)

    print("Opening Apec job page...")

    page.goto(
        detail_url,
        wait_until="networkidle"
    )

    browser.close()


if detail_data is None:
    print("\nNo successful detail response captured.")
else:
    print("\n--- TOP-LEVEL DETAIL FIELDS ---")

    for key in detail_data.keys():
        print(key)