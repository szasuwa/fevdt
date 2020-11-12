import requests
import re
import urllib.parse

def extractUrlData(url):
    parsed = urllib.parse.urlparse(url)
    baseUrl = "%s://%s/" % (parsed.scheme, parsed.netloc)
    basePathUrl = "%s://%s%s/" % (parsed.scheme, parsed.netloc, "/".join(parsed.path.split("/")[:-1]))
    return [baseUrl, basePathUrl]

def getSiteScriptList(url):
    page = requests.get(url)
    scripts = re.findall(r'<script[^>]+>\s*</script>', page.text)

    output = []
    for script in scripts:
        lib = re.search(r'(?<=src=[\'\"])[^\"]+(\.js)[^\'\"]*', script)

        if lib is None:
            continue

        scriptUrl = lib.group()
        if scriptUrl.startswith("."):
            scriptUrl = urllib.parse.urljoin(url, scriptUrl)

        output.append(scriptUrl)

    return output

def extractLibData(url):
    return extractLibDataFromUrl(url)

def extractLibDataFromUrl(url):
    primaryName = re.sub("(\.min)|(\.js)|(\?\S+)", "", url.split("/")[-1])
    versions = re.findall(r'(?<=[^\w])(\d+(?:\.\d+)+)', url)
    possibleNames = url.split("/")[3:-2]
    return [url, primaryName, versions, possibleNames]

#list = getSiteScriptList("https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n")
#list = getSiteScriptList("https://stronylabaz.pl")

list = ["https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js", "https://s.student.pwr.edu.pl/iwc_static/c11n/js/bootstrap.js","https://s.student.pwr.edu.pl/iwc_static/js/dojotoolkit/dojo/dojo.js?3.0.1.3.0_16070546", "https://www.stronylabaz.pl/wp-content/plugins/cookie-notice/js/front.min.js?ver=1.3.2", "https://c0.wp.com/c/5.5.3/wp-includes/js/jquery/jquery.js", "https://www.stronylabaz.pl/wp-content/plugins/revslider/public/assets/js/rbtools.min.js?ver=6.2.23", "https://www.stronylabaz.pl/wp-content/plugins/revslider/public/assets/js/rs6.min.js?ver=6.2.23", "https://c0.wp.com/p/jetpack/9.0.2/_inc/build/photon/photon.min.js", "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/mcw_fp_js-vb00bca612da7bafe0e2bbef1cd7c3d8955c5a003.js", "https://www.google.com/recaptcha/api.js?render=6LcBlvUUAAAAAMBggM51EaDhc_hKGjSHtoDNjfx1&#038;ver=3.0", "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/wpcf7-recaptcha-vd046ebdf801d8c73a1c6d7a5e6f13365826058d6.js", "https://www.stronylabaz.pl/wp-content/themes/page-builder-framework/js/min/site-min.js?ver=2.5.9", "https://www.stronylabaz.pl/wp-content/plugins/js_composer/assets/js/dist/js_composer_front.min.js?ver=6.4.1", "https://www.stronylabaz.pl/wp-content/plugins/js_composer/assets/lib/vc_waypoints/vc-waypoints.min.js?ver=6.4.1", "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.compatibility.min.js?ver=1", "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/smart-sections-vb840001bc8643d11a20dcc548966140ca9a3f96f.js", "https://www.stronylabaz.pl/wp-content/plugins/visucom-smart-sections/assets/js/salvattore.min.js?ver=1", "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/loop-v3968f667e26e85069ef909a6c3f0135f11f7c777.js", "https://stats.wp.com/e-202046.js"]

for i in list:
    x = extractLibData(i)

    print("--- Result ---")
    print("Url:", x[0])
    print("Primary Name: ", x[1])
    print("Versions: ", x[2])
    print("Path names: ", x[3])

