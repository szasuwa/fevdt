import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
import math
import csv
import xlsxwriter


def fetch_nvd_page(query):
    output = []
    idx_max = 1
    idx_current = 0
    safe_query = urllib.parse.quote(query)

    while idx_current < idx_max:
        url = 'https://nvd.nist.gov/vuln/search/results?query=%s&startIndex=%i' % (safe_query, idx_current)
        print(url)
        site = requests.get(url)
        idx_max = int(re.search(r'(?<=data-testid="vuln-matching-records-count">)\d+[,]?\d*', site.text).group().replace(",", ""))
        idx_current = int((re.search(r'(?<=data-testid="vuln-displaying-count-through">)\d+[,]?\d*', site.text).group()).replace(",", ""))
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


def export_to_csv(filename, tab):
    row = ["CVE ID", "Description", "Published Date", "Severity 3.0", "Severity 2.0"]
    tab.insert(0, row)
    with xlsxwriter.Workbook(filename + '.xlsx') as workbook:
        worksheet = workbook.add_worksheet()
        for row_num, data in enumerate(tab):
            worksheet.write_row(row_num, 0, data)


tmp = fetch_nvd_page("cpe:2.3:*:*:jquery:2.1.4")
print(len(tmp))
for x in tmp:
    print(x)
export_to_csv("testFile", tmp)