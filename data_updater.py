import json
import pycountry
import requests

def get_country_data():
    """Fetches country data from the World Bank API and saves it to a JSON file."""
    countries = {}
    for country in pycountry.countries:
        countries[country.name] = {
            "alpha_2": country.alpha_2,
            "alpha_3": country.alpha_3,
            "numeric": country.numeric,
        }
    with open("countries.json", "w") as f:
        json.dump(countries, f, indent=4)

def get_income_levels():
    """Fetches income level data from the World Bank API and saves it to a JSON file."""
    url = "http://api.worldbank.org/v2/country?format=json"
    response = requests.get(url)
    data = response.json()
    income_levels = {}
    for country in data[1]:
        income_levels[country["name"]] = {
            "incomeLevel": country["incomeLevel"]["value"],
            "capitalCity": country["capitalCity"],
            "longitude": country["longitude"],
            "latitude": "latitude",
        }
    with open("income_levels.json", "w") as f:
        json.dump(income_levels, f, indent=4)

if __name__ == "__main__":
    get_country_data()
    get_income_levels()
