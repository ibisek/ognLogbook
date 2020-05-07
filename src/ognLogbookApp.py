

from ogn.client import AprsClient
from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from beaconProcessor import BeaconProcessor

bp = BeaconProcessor()


def process_beacon(raw_message):
    # print("RAW:", raw_message)

    # throw away other types of messages to increase performance:
    if raw_message[:3] not in ['OGN', 'FLR', 'ICA']:
        return

    beacon = None
    try:
        beacon = parse(raw_message)
        if 'beacon_type' in beacon.keys() and beacon['beacon_type'] == 'aprs_aircraft':
            # print("BEACON: ", beacon)
            bp.enqueueForProcessing(beacon)

    except ParseError as e:
        print('[ERROR] {}'.format(e.message))
        if beacon:
            print("Failed BEACON:", beacon)

    except Exception as e:
        # print('[ERROR] {}'.format(e))
        # if beacon:
        #     print("Failed BEACON:", beacon)
        pass


if __name__ == '__main__':
    aprsFilter = 'r/+49.3678/+16.1145/300'
    # aprsFilter = None

    client = AprsClient(aprs_user='ibisek', aprs_filter=aprsFilter)
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
