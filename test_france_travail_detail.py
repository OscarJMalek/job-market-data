from scrapers.france_travail import (
    scrape_france_travail_detail,
)


url = (
    "https://candidat.francetravail.fr"
    "/offres/recherche/detail/212RNCS"
)

job = scrape_france_travail_detail(url)

print("\n--- STRUCTURED JOB ---")

print("Source job ID:", job.get("source_job_id"))
print("Title:", job.get("title"))
print("Company:", job.get("company"))
print("Location:", job.get("location"))
print("City:", job.get("city"))
print("Region:", job.get("region"))
print("Country:", job.get("country"))
print("Posted at:", job.get("posted_at"))
print("Contract:", job.get("contract_text"))
print("Working time:", job.get("working_time_text"))
print("Salary:", job.get("salary_text"))
print("URL:", job.get("url"))

print("\n--- DESCRIPTION ---")

description = job.get("description")

if description:
    print(description[:2000])
else:
    print("No description found.")