import re


APEC_CONTRACT_TYPES = {
    101887: "CDD",
    101888: "CDI",
    101889: "Mission d'intérim",
    597139: "CDI - Alternance - Contrat d'apprentissage",
}


APEC_TELEWORK_TYPES = {
    20765: "Télétravail partiel possible",
    20766: "Télétravail ponctuel autorisé",
    20767: "Télétravail total possible",
    20949: "Pas de télétravail autorisé",
}


def parse_apec_department(location):
    if not location:
        return None

    parts = location.rsplit(" - ", 1)

    if len(parts) == 2:
        department = parts[1].strip()

        if department.isdigit():
            return department

    return None


def parse_apec_salary(salary_text):
    if not salary_text:
        return None, None

    salary_text = salary_text.strip()

    if salary_text == "A négocier":
        return None, None

    # Example: "40 - 45 k€ brut annuel"
    range_match = re.match(
        r"^(\d+)\s*-\s*(\d+)\s*k€",
        salary_text
    )

    if range_match:
        salary_min = int(range_match.group(1)) * 1000
        salary_max = int(range_match.group(2)) * 1000

        return salary_min, salary_max

    # Example: "A partir de 35 k€ brut annuel"
    minimum_match = re.match(
        r"^A partir de\s+(\d+)\s*k€",
        salary_text
    )

    if minimum_match:
        salary_min = int(minimum_match.group(1)) * 1000

        return salary_min, None

    return None, None


def transform_apec_job(job, sector_mapping):
    contract_code = job.get("typeContrat")
    telework_code = job.get("idNomTeletravail")
    sector_code = job.get("secteurActivite")

    salary_min, salary_max = parse_apec_salary(
        job.get("salaireTexte")
    )

    department = parse_apec_department(
        job.get("lieuTexte")
    )

    sector = sector_mapping.get(sector_code)

    return {
        "title": job.get("intitule"),
        "company": job.get("nomCommercial"),
        "location": job.get("lieuTexte"),
        "department": department,
        "sector": sector,
        "job_type": APEC_CONTRACT_TYPES.get(contract_code),
        "work_mode": APEC_TELEWORK_TYPES.get(telework_code),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_text": job.get("salaireTexte"),
        "salary_currency": "EUR",
        "description": job.get("texteOffre"),
        "source": "APEC",
        "source_job_id": job.get("numeroOffre"),
        "url": (
            "https://www.apec.fr/candidat/recherche-emploi.html/emploi/"
            f"detail-offre/{job.get('numeroOffre')}"
        ),
        "posted_at": job.get("datePublication"),
        "status": "active",
    }