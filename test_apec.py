import requests
import re

base_url = "https://www.apec.fr"

js_url = (
    base_url
    + "/modules/apec-jahia-module/javascript/angular-output/"
      "offres/dist/main-MLZVUHH6.js"
)

response = requests.get(js_url)

print("Status code:", response.status_code)
print("Content length:", len(response.text))

js = response.text

# Look for anything that looks like an Apec backend endpoint
patterns = [
    r'["\'](/cms/webservices[^"\']*)["\']',
    r'["\'](/cms/webservice[^"\']*)["\']',
    r'["\']([^"\']*recherche[^"\']*)["\']',
    r'["\']([^"\']*offres[^"\']*)["\']',
]

matches = set()

for pattern in patterns:
    for match in re.findall(pattern, js, re.IGNORECASE):
        matches.add(match)

print("\n--- POTENTIAL ENDPOINTS ---")

for match in sorted(matches):
    print(match)

print("\nTotal matches:", len(matches))