import requests
import re

# URL = 'https://s.student.pwr.edu.pl/iwc_static/c11n/login_student_pwr_edu_pl.html?lang=pl&3.0.1.3.0_16070546&svcs=abs,mail,calendar,c11n'
# page = requests.get(URL)

pg = open("page.txt", "r", encoding="UTF-8")
content = pg.read().rstrip()
pg.close()


for match in re.findall(r'<script[^>]+>\s*</script>', content):
    lib = re.search(r'(?<=[/"])[^/]+(?=\.js)', match)

    if lib is None:
        continue

    lib = lib.group()
    ver = re.search(r'(\.?\d+)+', match)

    if ver is not None:
        ver = ver.group()

    if lib.endswith(".min"):
        if ver is None:
            version = "min"

        lib = lib.split(".")[0]

    print('=== Lib ===')
    print("Match:", match)
    print("Possible Lib:", lib)
    print("Possible Version:", ver)

    if ver is None or ver == "min":
        print("CPE:", "cpe:2.3:*:*:%s" % (lib))
    else:
        print("CPE:", "cpe:2.3:*:*:%s:%s" % (lib, ver))


