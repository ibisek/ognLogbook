
import os
import sys
import signal
import time
from socket import SHUT_RDWR

from ogn.client import AprsClient

from configuration import APRS_FILTER
from beaconProcessor import BeaconProcessor

bp = BeaconProcessor()
doRun = True
client: AprsClient = AprsClient(aprs_user='ibisek', aprs_filter=APRS_FILTER)


def process_beacon(raw_message):
    # print("RAW:", raw_message)

    # throw away other types of messages to increase performance:
    if raw_message[:3] not in ['OGN', 'FLR', 'ICA']:
        return

    bp.enqueueForProcessing(raw_message)


def signal_handler(sig, frame):
    print('SIGINT / Ctrl+C detected!')

    bp.stop()

    global doRun
    doRun = False

    if client:
        print("XX killing the client")
        client._kill = True
        client.autoreconnect = False
        client.sock.setblocking(False)
        client.disconnect()
        client.sock.shutdown(SHUT_RDWR)     # force the client to stop!
        client.sock.close()         # force the client to stop!

    print('[INFO] Shutdown initiated')
    time.sleep(4)
    sys.exit(0)
    print('KOHEU.')


if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)

    while doRun:
        try:
            client.connect()
            client.run(callback=process_beacon, autoreconnect=True)
            print("XX CLIENT 2")
        except KeyboardInterrupt:
            print('\nApp interrupted.')
            client.disconnect()
            doRun = False
        except TimeoutError as ex:
            print("ERROR:", str(ex))

    print('[INFO] Quitting the APP.')
    sys.exit(0)
