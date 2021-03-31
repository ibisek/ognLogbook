
import sys
import time
from socket import SHUT_RDWR

from ogn.client import AprsClient
from ogn.parser import parse, AprsParseError

from configuration import APRS_FILTER, DEBUG
from beaconProcessor import BeaconProcessor
from cron.cronJobs import CronJobs

bp = BeaconProcessor()
doRun = True
client: AprsClient = AprsClient(aprs_user='ibisek', aprs_filter=APRS_FILTER)
cron = CronJobs()


def process_beacon(raw_message):
    # print("RAW:", raw_message)

    # accept only supported types of messages:
    if raw_message[:3] in ['OGN', 'FLR', 'ICA']:
        bp.enqueueForProcessing(raw_message)

    elif DEBUG:
        try:
            if raw_message[:3] in ['PAW', 'RND']:  # # PAW (PilotAWare), RND(?) (not decided if they are worth processing yet)
                return

            beacon = parse(raw_message)
            if 'beacon_type' in beacon:
                bType = beacon['beacon_type']
                if bType in ['aprs_aircraft']:  # still an aircraft, right?
                    print('## ACFT BCN:', beacon)

                elif bType not in ('unknown', 'receiver', 'fanet', 'aprs_receiver', 'pilot_aware', 'flymaster'):
                    print('## TYPE:', bType, '\t\t', beacon)

        except AprsParseError:
            pass


def _cleanup():
    bp.stop()
    cron.stop()

    global doRun
    doRun = False

    if client:
        client.disconnect()

        # the client doesn't want to quit..
        client._kill = True
        client.autoreconnect = False
        client.sock.setblocking(False)
        client.sock.shutdown(SHUT_RDWR)     # force the client to stop!
        client.sock.close()         # force the client to stop!
        # .. all this doesn't help anyway.

    time.sleep(4)


# def signal_handler(sig, frame):
#     print('SIGINT / Ctrl+C detected!')
#     _cleanup()
#     sys.exit(0)


if __name__ == '__main__':

    # disabled as this obviously prevents the client to be terminated:
    # signal.signal(signal.SIGINT, signal_handler)

    while doRun:
        try:
            print('[INFO] Connecting to OGN APRS server..')
            client.connect()
            client.run(callback=process_beacon, autoreconnect=False)
            print('[WARN] Connection to OGN APRS server lost!')
            time.sleep(4)   # not to cause a DDOS on the OGN servers
        except KeyboardInterrupt:
            print('\n[INFO] Application interrupted.')
            try:
                client.disconnect()
            except Exception as ex:
                print('[ERROR] on client.disconnect():', str(ex))
            doRun = False
        except TimeoutError as ex:
            print('[ERROR] Timeout:', str(ex))
        except ConnectionError as ex:
            print('[ERROR] Connection:', str(ex))
        except BrokenPipeError as ex:
            print('[WARN] broken pipe:', str(ex))
        except Exception as ex:
            print('ANOTHER ERROR:', str(ex))

    print('[INFO] Quitting the APP.')
    _cleanup()
    sys.exit(0)
