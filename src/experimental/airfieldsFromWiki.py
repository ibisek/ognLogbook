
INDEX_URL_TEMPLATE = "https://en.wikipedia.org/wiki/List_of_airports_by_ICAO_code:_{}"
DETAIL_URL_TEMPLATE = "https://en.wikipedia.org/wiki/{}"

if __name__ == '__main__':

    for i in range(ord('A'), ord('Z')+1):
        # print(i, chr(i))

        url = INDEX_URL_TEMPLATE.format(chr(i))
        print('url1:', url)
        # TODO get the page

        # TODO parse a search for these:
        # <li>([A-Z]{4})\s.+?a href="(.+?)"
        icao = ""
        path = ""

        url = DETAIL_URL_TEMPLATE.format(path)
        print('url2:', url)

        # TODO search for:
        # <span class="geo-dec" title="Maps, aerial photos, and other data for this location">40.07250°N 116.59750°E</span><span style="display:none">﻿ / <span class="geo">40.07250; 116.59750</span></span></span></a>
        # <span class="geo">(.+?);(.+?)<\/span>




