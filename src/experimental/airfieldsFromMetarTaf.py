"""
@see https://metar-taf.com/country/russia?page=1
"""

import re
import json
import requests
from bs4 import BeautifulSoup

ROOT_URL_TEMPLATE = "https://metar-taf.com/country/russia?page={}"
AIRFIELD_URL_TEMPLATE = "https://metar-taf.com{}"

REGEX_COORDS1 = re.compile('located at.+?([0-9.]+).+?([0-9.]+)')


def readPage(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print('[ERROR] status:', response.status_code)

        return response.text

    except ConnectionError as e:
        pass
    except Exception as e:
        pass

    return None


if __name__ == '__main__':

    airfields = []

    for page in range(1, 29):
        print("page ", page)

        url = ROOT_URL_TEMPLATE.format(page)
        print('url1:', url)
        html = readPage(url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        divs = soup.find_all(name='div', id='w1')
        div = divs[0]

        rows = div.find_all(name='tr')
        for row in rows:
            tds = row.find_all(name='td')
            if len(tds) == 0:
                continue

            code = tds[0].text
            name = tds[1].text
            href = tds[1].find(name='a')['href']

            url2 = AIRFIELD_URL_TEMPLATE.format(href)
            print('url2:', url2)
            html2 = readPage(url2)
            if not html2:
                continue

            soup2 = BeautifulSoup(html2, 'html.parser')

            try:
                text = soup2.find(name='article').find(name='p').text
            except AttributeError as e:
                continue

            m = REGEX_COORDS1.findall(text)
            if m and len(m[0]) == 2:
                lat = float(m[0][0])
                lon = float(m[0][1].strip('.'))

                if lat and lon:
                    print(f'{code}; {lat:.6f}; {lon:.6f}')
                    d = {'code': code, 'lat': lat, 'lon': lon}
                    airfields.append(d)

    with open('../../data/airfields-metarTaf-Ru.json', 'w') as f:
        f.write(json.dumps(airfields))

    print('KOHEU.')
