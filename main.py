import requests
import re
from bs4 import BeautifulSoup
import math
import csv
import xlsxwriter
import urllib.parse

url_blacklist = [
    # Regex
    '/www.google.com/'
]

url_blacklist_regex = r'(%s)' % (")|(".join(url_blacklist))

lib_name_blacklist = [
    # Regex
    '(?<=[^\w])(\d+(?:\.\d+)+)',
    'libs?',
    'plugins?',
    'static',
    '^js$',
    'wp-.+',
    'build',
    '^.$',
    '_inc',
    'ajax',
    'cookies',
    'app'
]

url_framework = {
    # "framework" : { "regex": remove_from_urls }
    'wordpress': {
        'wp-content': True,
        'wp-includes': False
    }
}


def extract_url_data(url):
    parsed = urllib.parse.urlparse(url)
    base_url = "%s://%s/" % (parsed.scheme, parsed.netloc)
    base_path_url = "%s://%s%s/" % (parsed.scheme, parsed.netloc, "/".join(parsed.path.split("/")[:-1]))
    return [base_url, base_path_url]


def get_site_script_list(url):
    page = requests.get(url)
    scripts = re.findall(r'<script[^>]+>\s*</script>', page.text)

    output = []
    for script in scripts:
        lib = re.search(r'(?<=src=[\'\"])[^\"]+(\.js)[^\'\"]*', script)

        if lib is None:
            continue

        script_url = lib.group()
        if script_url.startswith("."):
            script_url = urllib.parse.urljoin(url, script_url)

        output.append(script_url)

    return output


def filter_script_list(url_list):
    if len(url_blacklist) <= 0 and len(url_framework) <= 0:
        return list

    output_url = []
    output_fwk = set()
    for url in url_list:
        if len(url_blacklist) > 0 and re.search(url_blacklist_regex, url) is not None:
            continue

        found_framework = False
        ignore_framework = False
        for fwk in url_framework:
            if found_framework is True:
                break

            for fwk_re in url_framework[fwk]:
                if re.search(fwk_re, url) is not None:
                    output_fwk.add(fwk)
                    found_framework = True
                    ignore_framework = url_framework[fwk][fwk_re]
                    break

        if found_framework is True and ignore_framework is True:
            continue

        output_url.append(url)

    return {"urls": output_url, "frameworks": output_fwk}


def extract_lib_data(url):
    return extract_lib_data_from_url(url)


def extract_possible_names(url):
    if len(lib_name_blacklist) <= 0:
        return reversed(url.split("/")[3:-1])

    url_split = reversed(url.split("/")[3:-1])
    blacklist_regex = r'(%s)' % (")|(".join(lib_name_blacklist))

    output = []
    for i in url_split:
        if re.search(blacklist_regex, i) is not None:
            continue

        output.append(i)

    return output


def extract_lib_data_from_url(url):
    primary_name = re.sub("([.-]min)|(\.js)|(\?\S+)", "", url.split("/")[-1])
    versions = set(re.findall(r'(?<=[^\w])(\d+(?:\.\d+)+)', url))

    tmp = re.match(r'(\S+)-(\d+(?:\.\d+)*)', primary_name)
    if tmp is not None:
        tmp = tmp.groups()
        primary_name = tmp[0]
        versions.add(tmp[1])

    blacklist_regex = r'(%s)' % (")|(".join(lib_name_blacklist))
    if re.search(blacklist_regex, primary_name) is not None:
        primary_name = None

    possible_names = set(extract_possible_names(url))
    return {"url": url, "primary_name": primary_name, "versions": versions, "secondary_names": possible_names}


def find_library_cpe_version(library, version):
    version_split = version.split(".")
    while len(version_split) > 0:
        if has_valid_cpe(library, ".".join(version_split)):
            return version_split

        version_split.pop()

    return None


def find_best_library_cpe(library, version):
    if has_valid_cpe(library, None) is False:
        return None

    possible_versions = []
    for v in version:
        tmp = find_library_cpe_version(library, v)

        if tmp is not None:
            possible_versions.append(tmp)

    best_version = []

    for i in possible_versions:
        if len(best_version) < len(i):
            best_version = i

    return {"name": library, "version": best_version}


def find_cpe(result):
    if result["primary_name"] is not None:
        tmp = find_best_library_cpe(result["primary_name"], result["versions"])

        if tmp is not None:
            tmp2 = ".".join(tmp["version"]) if len(tmp["version"]) > 0 else None
            return {"name": tmp["name"], "version": tmp2, "cpe": build_cpe_string(tmp["name"], tmp2)}

    possible_cpe = []
    for path_name in result["secondary_names"]:
        tmp = find_best_library_cpe(path_name, result["versions"])

        if tmp is not None:
            possible_cpe.append(tmp)

    best_possible_cpe = {"name": None, "version": []}

    for i in possible_cpe:
        if len(best_possible_cpe["version"]) < len(i["version"]):
            best_possible_cpe = i

    if best_possible_cpe["name"] is None:
        return None
    else:
        tmp2 = ".".join(best_possible_cpe["version"]) if len(best_possible_cpe["version"]) > 0 else None
        return {"name": best_possible_cpe["name"], "version": tmp2, "cpe": build_cpe_string(best_possible_cpe["name"], tmp2)}


def build_cpe_string(library, version):
    cpe = "cpe:2.3:*:*:%s" % library
    if version is not None and len(version) > 0:
        cpe += ":%s" % version

    return cpe


def has_valid_cpe(library, version):
    url = 'https://nvd.nist.gov/products/cpe/search/results?namingFormat=2.3&keyword=%s' % (build_cpe_string(library, version))
    site = requests.get(url)
    result = int(re.search(r'(?<=data-testid="cpe-matching-records-count">)\d+', site.text).group())
    return result > 0


def filter_valid_cpe(url_list):
    output = []
    for url in url_list:
        extracted = extract_lib_data(url)
        tmp = find_cpe(extracted)

        if tmp is not None:
            output.append(tmp)

    return output


def fetch_nvd_page(query):
    output = []
    idx_max = 1
    idx_current = 0
    safe_query = urllib.parse.quote(query)

    while idx_current < idx_max:
        url = 'https://nvd.nist.gov/vuln/search/results?query=%s&startIndex=%i' % (safe_query, idx_current)
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


def analyze_url(url):
    detected = get_site_script_list(url)

    detected = filter_script_list(detected)
    cpe_list = filter_valid_cpe(detected["urls"])

    nvd = {"libraries": {}, "frameworks": {}}

    for cpe in cpe_list:
        nvd["libraries"]["%s-%s" % (cpe["name"], cpe["version"])] = fetch_nvd_page(cpe["cpe"])

    for framework in detected["frameworks"]:
        nvd["frameworks"][framework] = fetch_nvd_page(framework)

    print(nvd)
    # TODO: Output and saving


analyze_url("http://pwr.edu.pl")

# tmp = fetch_nvd_page("cpe:2.3:*:*:jquery:2.1.4")
# print(len(tmp))
# for x in tmp:
#     print(x)
# export_to_csv("testFile", tmp)
