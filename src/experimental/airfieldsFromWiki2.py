"""
This is to parse airstrips specifically in Canada.
@see https://en.wikipedia.org/wiki/List_of_airports_in_Canada

Optionally, we could later process also the
https://en.wikipedia.org/wiki/List_of_heliports_in_Canada
"""

import re
import json
import requests
from bs4 import BeautifulSoup

STRIP_URL_TEMPLATE = "https://en.wikipedia.org{}"

REGEX1 = re.compile('<li>([A-Z]{4}).+?a.+?href="(.+?)"')
REGEX2 = re.compile('<span class="geo">(.+?);(.+?)<\/span>')
REGEX_COORDS1 = re.compile('(\d+)[°](\d+)[′]([0-9.]+){0,1}[″]{0,1}([NSEW])')
REGEX_COORDS2 = re.compile('geohack.toolforge.org.+params=([0-9.]+)_([NS])_([0-9.]+)_([EW])')

URLS_LEVEL0 = [
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(A%E2%80%93B)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(C%E2%80%93D)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(E%E2%80%93G)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(H%E2%80%93K)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(L%E2%80%93M)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(N%E2%80%93Q)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(R%E2%80%93S)',
    'https://en.wikipedia.org/wiki/List_of_airports_in_Canada_(T%E2%80%93Z)',
]


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

    for url in URLS_LEVEL0:
        print('url:', url)
        html = readPage(url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        tables = soup.find_all('table', {'class': 'wikitable'})
        for table in tables:
            allRows = table.find_all('tr')

            for row in allRows:
                tds = row.findAll('td')
                if len(tds) == 0:
                    continue    # this is the table header

                subUrl = tds[0].find('a')['href']  # a link to the strip's wiki page
                icao = tds[1].text   # all with icao code shall already be in our db..
                tcLid = tds[2].text # Transport of Canada Location Id
                iata = tds[3].text   # IATA code.. useless for us (at this moment)

                url2 = STRIP_URL_TEMPLATE.format(subUrl)
                print('url2:', url2)

                html2 = readPage(url2)
                if not html2:
                    continue

                soup2 = BeautifulSoup(html2, 'html.parser')

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
                    print(f'{icao}; {tcLid}; {lat:.6f}; {lon:.6f}')
                    if tcLid:   # we shall already have the ICAO coded strips in the database
                        d = {'code': tcLid, 'lat': lat, 'lon': lon}
                        airfields.append(d)
                    elif icao:  # well, if there is no tcLid.. still keep it. When merging we will eliminate duplicates
                        d = {'code': icao, 'lat': lat, 'lon': lon}
                        airfields.append(d)

    with open('../../data/airfields-wikipedia-canada.json', 'w') as f:
        f.write(json.dumps(airfields))

    print('KOHEU.')
