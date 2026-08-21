import re


def parse_department(location):
    if not location:
        return None

    match = re.match(r"^(\d{2,3})\s*-\s*", location)

    if match:
        return match.group(1)

    return None


def parse_contract_type(contract_text):
    if not contract_text:
        return None

    text = contract_text.lower()

    if text.startswith("cdi"):
        return "CDI"

    if text.startswith("cdd"):
        return "CDD"

    if text.startswith("intérim"):
        return "Mission d'intérim"

    if text.startswith("profession libérale"):
        return "Profession libérale"

    return contract_text


def parse_salary(salary_text):
    if not salary_text:
        return None, None

    text = salary_text.replace("\n", " ")

    # Annual range
    match = re.search(
        r"Annuel de\s+([\d.]+)\s+Euros\s+à\s+([\d.]+)\s+Euros",
        text,
        re.IGNORECASE,
    )

    if match:
        return (
            int(float(match.group(1))),
            int(float(match.group(2))),
        )

    # Fixed annual salary
    match = re.search(
        r"Annuel de\s+([\d.]+)\s+Euros",
        text,
        re.IGNORECASE,
    )

    if match:
        salary = int(float(match.group(1)))
        return salary, salary

    # Monthly range -> annualise
    match = re.search(
        r"Mensuel de\s+([\d.]+)\s+Euros\s+à\s+([\d.]+)\s+Euros",
        text,
        re.IGNORECASE,
    )

    if match:
        return (
            int(float(match.group(1)) * 12),
            int(float(match.group(2)) * 12),
        )

    # Fixed monthly salary -> annualise
    match = re.search(
        r"Mensuel de\s+([\d.]+)\s+Euros",
        text,
        re.IGNORECASE,
    )

    if match:
        salary = int(float(match.group(1)) * 12)
        return salary, salary

    return None, None


def transform_france_travail_job(job):
    salary_min, salary_max = parse_salary(
        job.get("salary_text")
    )

    return {
        "title": job.get("title"),
        "company": job.get("company") or "Non renseigné",
        "location": job.get("location"),
        "department": parse_department(
            job.get("location")
        ),
        "sector": None,
        "job_type": parse_contract_type(
            job.get("contract_text")
        ),
        "work_mode": None,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_text": job.get("salary_text"),
        "salary_currency": "EUR",
        "description": job.get("description"),
        "source": "FRANCE_TRAVAIL",
        "source_job_id": job.get("source_job_id"),
        "url": job.get("url"),
        "posted_at": job.get("posted_at"),
        "status": "active",
    }