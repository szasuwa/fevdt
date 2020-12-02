import requests
import re
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
    'ajax'
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


def filter_script_list(list):
    if len(url_blacklist) <= 0 and len(url_framework) <= 0:
        return list

    output_url = []
    output_fwk = set()
    for url in list:
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

    return [output_url, output_fwk]


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
    versions = re.findall(r'(?<=[^\w])(\d+(?:\.\d+)+)', url)
    possible_names = extract_possible_names(url)
    return [url, primary_name, versions, possible_names]


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

    return [library, best_version]

def find_cpe(result):
    tmp = find_best_library_cpe(result[1], result[2])

    if tmp is not None:
        return [tmp[0], ".".join(tmp[1]), build_cpe_string(tmp[0], ".".join(tmp[1]))]

    possible_cpe = []
    for path_name in result[3]:
        tmp = find_best_library_cpe(path_name, result[2])

        if tmp is not None:
            possible_cpe.append(tmp)

    best_possible_cpe = [None, []]

    for i in possible_cpe:
        if len(best_possible_cpe[1]) < len(i[1]):
            best_possible_cpe = i

    if best_possible_cpe[0] is None:
        return None
    else:
        return [best_possible_cpe[0], ".".join(best_possible_cpe[1]), build_cpe_string(best_possible_cpe[0], ".".join(best_possible_cpe[1]))]


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


url_list = ["https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js",
            "https://s.student.pwr.edu.pl/iwc_static/c11n/js/bootstrap.js",
            "https://s.student.pwr.edu.pl/iwc_static/js/dojotoolkit/dojo/dojo.js?3.0.1.3.0_16070546",
            "https://www.stronylabaz.pl/wp-content/plugins/cookie-notice/js/front.min.js?ver=1.3.2",
            "https://c0.wp.com/c/5.5.3/wp-includes/js/jquery/jquery.js",
            "https://www.stronylabaz.pl/wp-content/plugins/revslider/public/assets/js/rbtools.min.js?ver=6.2.23",
            "https://www.stronylabaz.pl/wp-content/plugins/revslider/public/assets/js/rs6.min.js?ver=6.2.23",
            "https://c0.wp.com/p/jetpack/9.0.2/_inc/build/photon/photon.min.js",
            "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/mcw_fp_js-vb00bca612da7bafe0e2bbef1cd7c3d8955c5a003.js",
            "https://www.google.com/recaptcha/api.js?render=6LcBlvUUAAAAAMBggM51EaDhc_hKGjSHtoDNjfx1&#038;ver=3.0",
            "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/wpcf7-recaptcha-vd046ebdf801d8c73a1c6d7a5e6f13365826058d6.js",
            "https://www.stronylabaz.pl/wp-content/themes/page-builder-framework/js/min/site-min.js?ver=2.5.9",
            "https://www.stronylabaz.pl/wp-content/plugins/js_composer/assets/js/dist/js_composer_front.min.js?ver=6.4.1",
            "https://www.stronylabaz.pl/wp-content/plugins/js_composer/assets/lib/vc_waypoints/vc-waypoints.min.js?ver=6.4.1",
            "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.compatibility.min.js?ver=1",
            "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/smart-sections-vb840001bc8643d11a20dcc548966140ca9a3f96f.js",
            "https://www.stronylabaz.pl/wp-content/plugins/visucom-smart-sections/assets/js/salvattore.min.js?ver=1",
            "https://www.stronylabaz.pl/wp-content/cache/asset-cleanup/js/item/loop-v3968f667e26e85069ef909a6c3f0135f11f7c777.js",
            "https://stats.wp.com/e-202046.js"]

detected_libs = filter_script_list(url_list)

for i in detected_libs[1]:
    print("--- Framework detected ---")
    print("Framework: ", i)

for i in detected_libs[0]:
    x = extract_lib_data(i)

    print("--- Result ---")
    print("Url:", x[0])
    print("Primary Name: ", x[1])
    print("Versions: ", x[2])
    print("Path names: ", x[3])
    print("CPE:", find_cpe(x))
