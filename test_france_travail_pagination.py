import re

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://candidat.francetravail.fr"

first_url = (
    "https://candidat.francetravail.fr"
    "/offres/emploi/comptable/rhone/s12m1d69"
)

session = requests.Session()

# Step 1: load the real first page
first_response = session.get(
    first_url,
    timeout=60,
)

first_response.raise_for_status()

first_soup = BeautifulSoup(
    first_response.text,
    "html.parser"
)

print("First page:", first_response.url)
print("Cookies:", len(session.cookies))


# Step 2: find France Travail's own next-page link
next_link = None

for link in first_soup.find_all("a", href=True):
    text = link.get_text(" ", strip=True).lower()

    if "offres suivantes" in text:
        next_link = link["href"]
        break

print("Next link:", next_link)

if not next_link:
    raise RuntimeError("No next-page link found")


# Step 3: follow it using the SAME session
next_url = requests.compat.urljoin(
    first_response.url,
    next_link,
)

next_response = session.get(
    next_url,
    timeout=60,
)

next_response.raise_for_status()

print("Requested URL:", next_url)
print("Final URL:", next_response.url)


# Step 4: inspect job IDs
next_soup = BeautifulSoup(
    next_response.text,
    "html.parser"
)

job_ids = []

for link in next_soup.find_all("a", href=True):
    href = link["href"]

    if re.fullmatch(
        r"/offres/recherche/detail/[A-Z0-9]+",
        href
    ):
        job_ids.append(
            href.split("/")[-1]
        )

print("Jobs found:", len(job_ids))
print("First five IDs:", job_ids[:5])