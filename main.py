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

def createCSV(filename, tab):
    row = ["CVE ID", "Description", "Published Date", "Severity 3.0", "Severity 2.0"]
    tab.insert(0, row)
    with xlsxwriter.Workbook(filename + '.xlsx') as workbook:
        worksheet = workbook.add_worksheet()
        for row_num, data in enumerate(tab):
            worksheet.write_row(row_num, 0, data)

tmp = fetch_nvd_page("jquery")
print(len(tmp))
for x in tmp:
    print(x)
createCSV("testFile", tmp)

def getSitePossibleLibList(url):
    page = requests.get(url)
    scripts = re.findall(r'<script[^>]+>\s*</script>', page.text)

    output = []
    for script in scripts:
        lib = re.search(r'(?<=[/"])[^/]+(?=\.js)', script)

        if lib is None:
            continue

        lib = lib.group()
        ver = re.search(r'(\.?\d+)+', script)

        if ver is not None:
            ver = ver.group()

        if lib.endswith(".min"):
            if ver is None:
                ver = "min"

            lib = lib[:-4]

        output.append([script, lib, ver])

    return output

def buildCpe(lib, ver):
    cpe = "cpe:2.3:*:*:%s" % lib
    if ver is not None and len(ver) > 0:
        cpe += ":%s" % ver

    return cpe

def findCpe(lib):
    name = lib[1]
    ver = lib[2]
    cpe = ""
    while True:
        while True:
            cpe = buildCpe(name, ver)
            site = requests.get("https://nvd.nist.gov/products/cpe/search/results?namingFormat=2.3&keyword=%s" % urllib.parse.quote(cpe))
            result = re.search(r'(?<=<strong data-testid="cpe-matching-records-count">)\d+(?=<\/strong>)', site.text).group()
            if int(result) > 0:
                return cpe

            if ver is None:
                ver = lib[2]
                break

            if ver.find(".") > 0:
                ver = ".".join((ver.split(".")[:-1]))
            else:
                ver = None

        if name is not None and name.find(".") > 0:
            name = ".".join((name.split(".")[:-1]))
        elif ver is not None and ver.find("-") > 0:
            ver = "-".join((name.split("-")[:-1]))
        else:
            return None

    return None

def printLib(lib):
    print('=== Lib ===')
    print("Match:", lib[0])
    print("Possible Lib:", lib[1])
    print("Possible Version:", lib[2])

list = getSitePossibleLibList("https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n")
