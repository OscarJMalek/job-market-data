import requests

search_url = "https://candidat.francetravail.fr/offres/recherche?lieux=69D&motsCles=finance&offresPartenaires=true&rayon=10&tri=0"

response = requests.get(search_url)

print("Status code:", response.status_code)
print("Content length:", len(response.text))

from bs4 import BeautifulSoup
import re


soup = BeautifulSoup(response.text, "html.parser")

print("Status code:", response.status_code)
print("Content length:", len(response.text))

print("\n--- PAGE TITLE ---")
print(soup.title.get_text(strip=True))

print("\n--- JOB OFFERS ---")

job_links = []

for link in soup.find_all("a", href=True):
    href = link["href"]

    if re.fullmatch(r"/offres/recherche/detail/[A-Z0-9]+", href):
        job_links.append(link)

print("Jobs found:", len(job_links))

for link in job_links[:20]:
    href = link["href"]
    text = link.get_text(" ", strip=True)

    offer_id = href.split("/")[-1]

    print(f"\nID: {offer_id}")
    print(f"Text: {text[:250]}")
    print(f"URL: https://candidat.francetravail.fr{href}")

print("\n--- PAGINATION LINKS ---")

for link in soup.find_all("a", href=True):
    href = link["href"]
    text = link.get_text(" ", strip=True)

    if any(
        keyword in href.lower()
        for keyword in ["page", "pagination", "suivant", "resultat"]
    ):
        print(f"{text[:100]} -> {href}")

next_page_url = (
    "https://candidat.francetravail.fr"
    "/offres/recherche.rechercheoffre:afficherplusderesultats/20-39/0"
    "?lieux=69D&motsCles=finance&offresPartenaires=true&rayon=10&tri=0"
)

next_response = requests.get(next_page_url)

print("\n--- NEXT PAGE TEST ---")
print("Status code:", next_response.status_code)
print("Content length:", len(next_response.text))

next_soup = BeautifulSoup(
    next_response.text,
    "html.parser"
)

next_job_links = []

for link in next_soup.find_all("a", href=True):
    href = link["href"]

    if re.fullmatch(r"/offres/recherche/detail/[A-Z0-9]+", href):
        next_job_links.append(link)

print("Jobs found:", len(next_job_links))

for link in next_job_links[:5]:
    href = link["href"]
    offer_id = href.split("/")[-1]
    text = link.get_text(" ", strip=True)

    print(f"{offer_id}: {text[:120]}")