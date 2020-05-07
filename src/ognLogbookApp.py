

from ogn.client import AprsClient
from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from beaconParser import BeaconParser

bp = BeaconParser()


def process_beacon(raw_message):
    print("   RAW:", raw_message)
    # if raw_message[0] == '#':
    #     print('Server Status: {}'.format(raw_message))
    #     return

    beacon = None
    try:
        beacon = parse(raw_message)
        if 'beacon_type' in beacon.keys() and beacon['beacon_type'] == 'aprs_aircraft':
            print("BEACON: ", beacon)

    except ParseError as e:
        print('Error, {}'.format(e.message))
        if beacon:
            print("Failed BEACON:", beacon)


if __name__ == '__main__':
    aprsFilter = 'r/+49.3678/+16.1145/200'  # distance from coords; 40 km je az do brna aby to bralo OGN cube

    client = AprsClient(aprs_user='ibisek', aprs_filter=aprsFilter)   #N0CALL
    client.connect()

    doRun = True
    while doRun:
        try:
            client.run(callback=process_beacon, autoreconnect=True)
        except KeyboardInterrupt:
            print('\nApp interrupted.')
            client.disconnect()
            doRun = False
        except TimeoutError as ex:
            print("ERROR:", str(ex))
