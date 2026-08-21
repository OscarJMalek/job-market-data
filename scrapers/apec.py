import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


APEC_URL = "https://www.apec.fr/cms/webservices/rechercheOffre"


def scrape_apec():

    payload = {
        "activeFiltre": True,
        "fonctions": [],
        "idNomZonesDeplacement": [],
        "idsEtablissement": [],
        "lieux": ["69"],
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

    all_jobs = []

    start_index = 0
    page_size = 20

    retry_strategy = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=2,
        allowed_methods={"POST"},
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    while True:

        payload["pagination"]["startIndex"] = start_index
        payload["pagination"]["range"] = page_size

        response = session.post(
            APEC_URL,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        jobs = data["resultats"]
        total_count = data["totalCount"]

        all_jobs.extend(jobs)

        print(
            f"APEC: fetched {len(jobs)} jobs "
            f"starting at {start_index}. "
            f"Total: {len(all_jobs)}/{total_count}"
        )

        start_index += page_size

        if start_index >= total_count:
            break
        time.sleep(1)

    return all_jobs