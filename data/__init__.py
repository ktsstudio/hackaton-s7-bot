from os import path
import csv

CURRENT_DIR = path.dirname(path.abspath(__file__))
CITIES = set()

with open(path.join(CURRENT_DIR, 'regions.csv'), 'r') as csvfile:
    rows = list(csv.reader(csvfile, delimiter=';', quotechar='|'))

    for row in rows:
        city = str(row[3]).strip().lower()
        if city:
            CITIES.add(city)