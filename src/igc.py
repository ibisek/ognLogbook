
from dataStructures import LogbookItem, addressPrefixes

IGC_HEADER_TEMPLATE = """AXXX LOGBOOK.IBISEK.COM
HFDTE{}
HFFXA000
HFPLTPILOTINCHARGE:
HFGTYGLIDERTYPE:{}
HFGIDGLIDERID:{}
HFDTM100GPSDATUM:WGS-1984
HFRFWFIRMWAREVERSION:
HFRHWHARDWAREVERSION:
HFFTYFRTYPE:
HFGPSGENERIC
HFPRSPRESSALTSENSOR:
HFCIDCOMPETITIONID:{}
I 01 36 38 GSP CR LF
"""


def flightToIGC(flightRecord: list, aircraftType='', registration='', competitionId='') -> str:
    """
    param flightRecord: flightRecord list of {'time': '2022-05-17T05:31:32Z', 'lat': 59.458233, 'lon': 13.344483, 'alt': 175.0, 'gs': 101.85, 'dt': datetime.datetime(2022, 5, 17, 5, 31, 32)}
    param aircraftType: e.g. 'Ls1-f'
    param registration: e.g. 'OK-1234'
    param competitionId: e.g. 'AF'
    """
    # https://xp-soaring.github.io/igc_file_format/index.html
    # https://xp-soaring.github.io/igc_file_format/igc_format_2008.html
    igcLines = []
    for fr in flightRecord:
        # B,095135, 4921993N,   01607080E,  A,  00000,  00489
        # B,TIME,   LAT,        LON,        A,  pAlt,   gpsAlt
        time = fr['dt'].strftime("%H%M%S")

        lat = fr['lat']
        latLetter = 'N' if lat >= 0 else 'S'
        lat = f"{lat:.5f}".replace('.', '')

        lon = fr['lon']
        lonLetter = 'E' if lon >= 0 else 'W'
        lon = f"{lon:.5f}".replace('.', '')

        alt = f"{fr['alt']:05.0f}"

        # extension to the B line defined by I line in the header
        # @see https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_I
        gs = f"{fr['gs']:03.0f}"

        line = f"B{time}{lat}{latLetter}{lon}{lonLetter}A{alt}{alt}{gs}"
        igcLines.append(line)

    date = flightRecord[0]['dt'].strftime("%d%m%y")     # format: DDMMYY
    igc = IGC_HEADER_TEMPLATE.format(date, aircraftType, registration, competitionId)
    igc += '\n'.join(igcLines)

    return igc
