import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
import math
import csv

# URL = 'https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n'
# page = requests.get(URL)

url = 'https://nvd.nist.gov/vuln/search/results?query=jquery&results_type=overview&form_type=Basic&search_type=all&startIndex=0'

#Function counts amount of pages
def findPageNum(url):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'lxml')
    line = soup.find('div', class_='col-sm-12 col-lg-3')
    cveNum = int(line.strong.text)
    pagesNum = math.ceil(cveNum/20)
    print(pagesNum)
    return pagesNum

#Function generate URLs that leads to next pages with vulnerabilities
def urlGenerator(pageNum, basicURL):
    urlTab = []
    basicURL = basicURL[:-1]
    index = str(0)
    for i in range(0, pageNum):
        urlTab.append(basicURL+index)
        index = str(int(index)+20)
    #print(urlTab)
    return urlTab


def parseSum(urlTab, sev2, sev3):
    sum = []
    i = 0
    for link in urlTab:
        print(link)
        page = requests.get(link).text
        soup = BeautifulSoup(page, 'lxml')
        for s in soup.find_all('tr'):
            if s.a is None:
                continue
            sum.append(s.a.text + " " + s.p.text + " " + s.span.text + " ")# + sev2[i-1] + " " + sev3[i-1])
            i = i + 1
    print(sum)
    return sum

def parseSeverity2(urlTab):
    severity2 = []
    for link in urlTab:
        page = requests.get(link).text
        soup = BeautifulSoup(page, 'lxml')
        for s in soup.find_all(id="cvss2-link"):
            if s.a is None:
                continue
            severity2.append("V2.0" + s.a.text)
    #print(severity2)
    return severity2

def parseSeverity3(urlTab):
    severity3 = []
    for link in urlTab:
        page = requests.get(link).text
        soup = BeautifulSoup(page, 'lxml')
        for s in soup.find_all(id="cvss3-link"):
            if s.a is None:
                continue
            severity3.append("V3.1: " + s.a.text)
    #print (severity3)
    return  severity3





#parseSeverity2(page)
#parseSeverity3(page)
pageNum = findPageNum(url)
urlTab = urlGenerator(pageNum, url)
parseSum(urlTab, parseSeverity2(urlTab), parseSeverity3(urlTab))

#-----------------------------------------------------------------------------------------#

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
