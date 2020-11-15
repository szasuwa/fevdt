import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
import math
import csv


def fetch_nvd_page(query):
    output = []
    idx_max = 1
    idx_current = 0
    while idx_current < idx_max:
        url = 'https://nvd.nist.gov/vuln/search/results?query=%s&results_type=overview&form_type=Basic&search_type=all&startIndex=%i' % (query, idx_current)
        site = requests.get(url)
        idx_max = int(re.search(r'(?<=data-testid="vuln-matching-records-count">)\d+', site.text).group())
        idx_current = int((re.search(r'(?<=data-testid="vuln-displaying-count-through">)\d+', site.text).group()))
        output += parse_nvd_page(site.text)

    return output


def parse_nvd_page(page):
    soup = BeautifulSoup(page, 'html.parser')
    output = []
    for s in soup.find_all('tr'):
        if s.a is None:
            continue

        row = [s.a.text, s.p.text, s.span.text, None, None]

        tmp = s.find(id="cvss2-link")
        if tmp is not None:
            row[3] = tmp.a.text

        tmp = s.find(id="cvss3-link")
        if tmp is not None:
            row[4] = tmp.a.text

        output.append(row)
    return output


tmp = fetch_nvd_page("jquery")
print(len(tmp))
for x in tmp:
    print(x)