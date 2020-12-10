"""
@see https://en.wikipedia.org/wiki/ICAO_airport_code
"""

import re
import json
import requests
from bs4 import BeautifulSoup

ROOT_URL_TEMPLATE = "https://en.wikipedia.org{}"
INDEX_URL_TEMPLATE = "https://en.wikipedia.org/wiki/List_of_airports_by_ICAO_code:_{}"

REGEX1 = re.compile('<li>([A-Z]{4}).+?a.+?href="(.+?)"')
REGEX2 = re.compile('<span class="geo">(.+?);(.+?)<\/span>')
REGEX_COORDS1 = re.compile('(\d+)[°](\d+)[′]([0-9.]+){0,1}[″]{0,1}([NSEW])')
REGEX_COORDS2 = re.compile('geohack.toolforge.org.+params=([0-9.]+)_([NS])_([0-9.]+)_([EW])')


def readPage(url: str) -> str:
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print('[ERROR] status:', response.status_code)

        return response.text

    except ConnectionError as e:
        pass
    except Exception as e:
        pass

    return None


def textCoordsToVal(coords: str) -> float:
    m = REGEX_COORDS1.match(coords)
    if m:
        deg = float(m.group(1))
        min = float(m.group(2))
        sec = float(m.group(3)) if m.group(3) else 0.0
        letter = m.group(4)
        sign = -1 if letter == 'S' or letter == 'W' else 1
        val = sign * (deg + min / 60 + sec / 3600)

        return val

    return None


def mapLinkToVal(link: str):
    m = REGEX_COORDS1.match(link)
    if m:
        lat = float(m.group(1))
        letter = m.group(2)
        sign = -1 if letter == 'S' or letter == 'W' else 1
        lat = sign * lat

        lon = float(m.group(3))
        letter = m.group(4)
        sign = -1 if letter == 'S' or letter == 'W' else 1
        lon = sign * lon

        return lat, lon

    return None, None


if __name__ == '__main__':

    airfields = []

    for i in range(ord('A'), ord('Z') + 1):
        # print(i, chr(i))

        url = INDEX_URL_TEMPLATE.format(chr(i))
        print('url1:', url)
        html = readPage(url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        lis = soup.find_all(name='li')
        for li in lis:
            m = REGEX1.findall(str(li))
            if m and len(m[0]) == 2:
                icao = m[0][0]
                path = m[0][1]

                url2 = ROOT_URL_TEMPLATE.format(path) if 'wikipedia.org' not in path else path
                if 'action=edit' in url2:
                    continue  # this link leads jut to an empty page

                print('url2:', url2)
                html2 = readPage(url2)
                if not html2:
                    continue

                soup2 = BeautifulSoup(html2, 'html.parser')
                lat = lon = None

                spans = soup2.find_all(name='span')
                latElement = soup2.find('span', {'class': 'latitude'})
                lonElement = soup2.find('span', {'class': 'longitude'})
                if latElement and lonElement:
                    lat = textCoordsToVal(latElement.text)
                    lon = textCoordsToVal(lonElement.text)

                else:  # parse the map link above the coordinates div
                    elements = soup.find_all('a', {'class': 'external text'})
                    for elem in elements:
                        if 'geohack' in str(elem):
                            lat, lon = mapLinkToVal(str(elem))

                if lat and lon:
                    print(f'{icao}; {lat:.6f}; {lon:.6f}')
                    d = {'code': icao, 'lat': lat, 'lon': lon}
                    airfields.append(d)

    with open('../../data/airfields-wikipedia.json', 'w') as f:
        f.write(json.dumps(airfields))

    print('KOHEU.')
