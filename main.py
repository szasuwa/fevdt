import requests
import urllib.parse
from bs4 import BeautifulSoup
import re

# URL = 'https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n'
# page = requests.get(URL)

pg = open("page.txt", "r", encoding="UTF-8")
content = pg.read().rstrip()
pg.close()

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

for i in list:
    printLib(i)
    print("CPE:", findCpe(i))


