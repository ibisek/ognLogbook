
import re

addressPattern = '"address":.?"(.+?)"'
addrRegex = re.compile(addressPattern, re.IGNORECASE)
gsPattern = '"ground_speed":.?(.+?),'
gsRegex = re.compile(gsPattern, re.IGNORECASE)

dtPattern = '"timestamp":(.*?), "'
dtRegex = re.compile(dtPattern, re.IGNORECASE)
atPattern = '"aircraft_type":.?(.+?),'
atRegex = re.compile(atPattern, re.IGNORECASE)
latPattern = '"latitude":.?(.+?),'
latRegex = re.compile(latPattern, re.IGNORECASE)
lonPattern = '"longitude":.?(.+?),'
lonRegex = re.compile(lonPattern, re.IGNORECASE)


def _parseInitialInfo(line: str):
    address = None
    groundSpeed = None

    m = addrRegex.search(line)
    if m:
        address = m.groups()[0]

    m = gsRegex.search(line)
    if m:
        groundSpeed = m.groups()[0]

    return address, groundSpeed


def _parseExtendedInfo(line):
    m = dtRegex.search(line)
    if m:
        dt = m.groups()[0]
        # TODO..

    m = atRegex.search(line)
    if m:
        aircraftType = m.groups()[0]

    m = latRegex.search(line)
    if m:
        lat = m.groups()[0]

    m = lonRegex.search(line)
    if m:
        lon = m.groups()[0]

    return dt, aircraftType, lat, lon


def parseLine(line):
    if 'aprs_aircraft' not in line:
        return

    # line = '{' + line[line.index('reference_timestamp')-1:]     # skip the "raw_message" section
    line = line.replace('\'', '"')
    print(line)

    # line = re.sub(r'(datetime.datetime\(.+?\))', "0", line)
    # print(line)

    address, groundSpeed = _parseInitialInfo(line)
    print(address, groundSpeed)

    currentStatus = 0 if groundSpeed < 30 else 1    # 0 = on ground, 1 = airborne

    # TODO query redis (ADDRESS_status)
    prevStatus = 1

    if currentStatus != prevStatus:
        # TODO update redis

        dt, aircraftType, lat, lon = _parseExtendedInfo(line)
        print(dt, aircraftType, lat, lon)

        # TODO create landed/departed SQL insert


if __name__ == '__main__':
    fn = '../data/1.line'
    with open(fn, 'r') as f:
        line = f.read()
        parseLine(line)
        # process_beacon(line)

    print('KOHEU.')
