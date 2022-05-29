
from math import floor

from dataStructures import LogbookItem, addressPrefixes

IGC_HEADER_TEMPLATE = """AOGN001
HFDTE{}
HFFXA000
HFPLTPILOTINCHARGE:
HFGTYGLIDERTYPE:{}
HFGIDGLIDERID:{}
HFDTM100GPSDATUM:WGS-1984
HFRFWFIRMWAREVERSION:
HFRHWHARDWAREVERSION:
HFFTYFRTYPE: logbook.ibisek.com
HFGPSGENERIC
HFPRSPRESSALTSENSOR:
HFCIDCOMPETITIONID:{}
I033638GSP
"""


def flightToIGC(flightRecord: list, aircraftType='', registration='', competitionId='') -> str:
    """
    param flightRecord: flightRecord list of {'time': '2022-05-17T05:31:32Z', 'lat': 59.458233, 'lon': 13.344483, 'alt': 175.0, 'gs': 101.85, 'dt': datetime.datetime(2022, 5, 17, 5, 31, 32)}
    param aircraftType: e.g. 'Ls1-f'
    param registration: e.g. 'OK-1234'
    param competitionId: e.g. 'AF'
    """
    if not aircraftType:
        aircraftType = ''
    if not registration:
        registration = ''
    if not competitionId:
        competitionId = ''

    # https://xp-soaring.github.io/igc_file_format/index.html
    # https://xp-soaring.github.io/igc_file_format/igc_format_2008.html
    igcLines = []
    for fr in flightRecord:
        # B,095135, 4921993N,   01607080E,  A,  00000,  00489
        # B,TIME,   LAT,        LON,        A,  pAlt,   gpsAlt
        time = fr['dt'].strftime("%H%M%S")

        # latitude: 8 bytes (including the letter) DDMMmmmN/S
        lat = fr['lat']
        deg = f"{abs(floor(lat)):02}"
        min = f"{(lat - floor(lat)) * 60:06.3f}"
        latLetter = 'N' if lat >= 0 else 'S'
        latStr = f"{deg}{min}{latLetter}".replace('.', '')

        # longitude: 9 bytes (including the letter) DDDMMmmmE/W
        lon = fr['lon']
        deg = f"{abs(floor(lon)):03}"
        min = f"{(lon - floor(lon)) * 60:06.3f}"
        lonLetter = 'E' if lon >= 0 else 'W'
        lonStr = f"{deg}{min}{lonLetter}".replace('.', '')

        alt = f"{fr['alt']:05.0f}"

        # extension to the B line defined by I line in the header
        # @see https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_I
        gs = f"{fr['gs']:03.0f}"

        line = f"B{time}{latStr}{lonStr}A{alt}{alt}{gs}"
        igcLines.append(line)

    date = flightRecord[0]['dt'].strftime("%d%m%y")     # format: DDMMYY
    igc = IGC_HEADER_TEMPLATE.format(date, aircraftType, registration, competitionId)
    igc += '\n'.join(igcLines)

    return igc
