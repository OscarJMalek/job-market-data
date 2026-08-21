import requests


reference_url = (
    "https://www.apec.fr"
    "/cms/webservices/referentielstatique/visuel"
)

sector_code = 101606

presentation_codes = [
    "NAF_700_SERVICE_DOMAIN",
    "DEMANDE_SECTEUR_ACTIVITE",
    "CRITERE_CADRE_SECTEUR_ACTIVITE_SERVICE_DOMAIN",
]

for presentation_code in presentation_codes:
    response = requests.get(
        reference_url,
        params={
            "presentationCode": presentation_code,
            "nomenclatureId": sector_code,
        },
    )

    print(f"\n--- {presentation_code} ---")
    print("Status:", response.status_code)
    print("Response:", response.text)