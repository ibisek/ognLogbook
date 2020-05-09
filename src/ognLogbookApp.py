

from ogn.client import AprsClient

from beaconProcessor import BeaconProcessor

bp = BeaconProcessor()


def process_beacon(raw_message):
    # print("RAW:", raw_message)

    # throw away other types of messages to increase performance:
    if raw_message[:3] not in ['OGN', 'FLR', 'ICA']:
        return

    bp.enqueueForProcessing(raw_message)


if __name__ == '__main__':
    aprsFilter = 'r/+49.3678/+16.1145/250'
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
