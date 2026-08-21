import re
import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://candidat.francetravail.fr"


def build_session():
    retry_strategy = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    return session


def extract_job_links(soup):
    jobs = []

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if not re.fullmatch(
            r"/offres/recherche/detail/[A-Z0-9]+",
            href
        ):
            continue

        offer_id = href.split("/")[-1]

        jobs.append(
            {
                "source_job_id": offer_id,
                "url": f"{BASE_URL}{href}",
                "search_result_text": link.get_text(
                    " ",
                    strip=True
                ),
            }
        )

    return jobs


def scrape_france_travail_search(search_name, search_url):
    all_jobs = []
    seen_ids = set()

    session = build_session()

    current_url = search_url
    page_number = 1

    while current_url:
        response = session.get(
            current_url,
            timeout=60,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        jobs = extract_job_links(soup)

        new_jobs = []

        for job in jobs:
            job_id = job["source_job_id"]

            if job_id not in seen_ids:
                seen_ids.add(job_id)
                new_jobs.append(job)

        all_jobs.extend(new_jobs)

        print(
            f"France Travail [{search_name}]: "
            f"page {page_number} returned {len(jobs)} jobs, "
            f"{len(new_jobs)} new. "
            f"Unique total: {len(all_jobs)}"
        )

        if not jobs:
            print(
                f"France Travail [{search_name}]: "
                "no jobs returned. Stopping."
            )
            break

        if jobs and not new_jobs:
            print(
                f"France Travail [{search_name}]: "
                "page contained no new jobs. Stopping."
            )
            break

        next_link = None

        for link in soup.find_all("a", href=True):
            text = link.get_text(" ", strip=True).lower()

            if "offres suivantes" in text:
                next_link = link["href"]
                break

        if not next_link:
            print(
                f"France Travail [{search_name}]: "
                "no next-page link found. Finished."
            )
            break

        current_url = requests.compat.urljoin(
            response.url,
            next_link
        )

        page_number += 1

        time.sleep(2)

    return all_jobs


def clean_text(element):
    if not element:
        return None

    return element.get_text(
        " ",
        strip=True
    )


def get_dt_value(soup, label):
    label_element = soup.find(
        string=lambda text:
        text
        and text.strip() == label
    )

    if not label_element:
        return None

    dt = label_element.find_parent("dt")

    if not dt:
        return None

    dd = dt.find_next_sibling("dd")

    return clean_text(dd)


def scrape_france_travail_detail(url, session=None):
    if session is None:
        session = build_session()

    response = session.get(
        url,
        timeout=60,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    offer_id_element = soup.select_one(
        '[itemprop="identifier"] [itemprop="value"]'
    )

    title_element = soup.select_one(
        '[itemprop="title"]'
    )

    location_element = soup.select_one(
        '[itemprop="jobLocation"] [itemprop="name"]'
    )

    city_element = soup.select_one(
        '[itemprop="addressLocality"]'
    )

    region_element = soup.select_one(
        '[itemprop="addressRegion"]'
    )

    country_element = soup.select_one(
        '[itemprop="addressCountry"]'
    )

    posted_element = soup.select_one(
        '[itemprop="datePosted"]'
    )

    description_element = soup.select_one(
        '[itemprop="description"]'
    )

    offer_id = clean_text(offer_id_element)
    title = clean_text(title_element)
    location = clean_text(location_element)

    city = (
        city_element.get("content")
        if city_element
        else None
    )

    region = (
        region_element.get("content")
        if region_element
        else None
    )

    country = (
        country_element.get("content")
        if country_element
        else None
    )

    posted_at = (
        posted_element.get("content")
        if posted_element
        else None
    )

    description = (
        description_element.get_text(
            "\n",
            strip=True
        )
        if description_element
        else None
    )

    contract_type = get_dt_value(
        soup,
        "Type de contrat"
    )

    working_time = get_dt_value(
        soup,
        "Durée du travail"
    )

    salary = get_dt_value(
        soup,
        "Salaire"
    )

    employer = None

    employer_heading = soup.find(
        lambda tag:
        tag.name == "h2"
        and tag.get_text(" ", strip=True) == "Employeur"
    )

    if employer_heading:
        employer_name = employer_heading.find_next(
            "h3",
            class_="t4 title"
        )

        if employer_name:
            employer = clean_text(employer_name)

    return {
        "source_job_id": offer_id,
        "title": title,
        "company": employer,
        "location": location,
        "city": city,
        "region": region,
        "country": country,
        "posted_at": posted_at,
        "description": description,
        "contract_text": contract_type,
        "working_time_text": working_time,
        "salary_text": salary,
        "url": url,
    }