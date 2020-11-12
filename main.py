import requests
import re
import urllib.parse

def extractUrlData(url):
    parsed = urllib.parse.urlparse(url)
    baseUrl = "%s://%s/" % (parsed.scheme, parsed.netloc)
    basePathUrl = "%s://%s%s/" % (parsed.scheme, parsed.netloc, "/".join(parsed.path.split("/")[:-1]))
    return [baseUrl, basePathUrl]

def getSiteScriptList(url):
    baseUrl = extractUrlData(url)

    page = requests.get(url)
    scripts = re.findall(r'<script[^>]+>\s*</script>', page.text)

    output = []
    for script in scripts:
        lib = re.search(r'(?<=src=[\'\"])[^\"]+(\.js)[^\'\"]*', script)

        if lib is None:
            continue

        scriptUrl = lib.group()
        if scriptUrl.startswith("."):
            scriptUrl = "%s%s" % (baseUrl[1], scriptUrl)

        output.append(scriptUrl)

    return output

list = getSiteScriptList("https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n")
#list = getSiteScriptList("https://stronylabaz.pl")

for i in list:
    print(i)

