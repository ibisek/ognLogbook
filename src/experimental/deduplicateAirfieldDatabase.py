
import json
import re

from airfieldManager import AirfieldManager
from dataStructures import Units

REGEX1 = re.compile('([A-Z]{2}-[0-9]{4})')
# REGEX1 = re.compile('([CZ]{2}-[0-9]{4})')

if __name__ == '__main__':

    am = AirfieldManager()

    recCodesToBeRemoved = []

    for code, rec in am.airfieldsDict.items():
        if REGEX1.match(code):
            removedRec = am.xxx_remove(rec.code)

            code2 = am.getNearest(rec.lat, rec.lon, units=Units.RAD)  # search for duplicates / nearest
            rec2 = am.get(code=code2)

            # _code3, _dist3 = am.getNearest2(rec.lat, rec.lon, units=Units.RAD, calcDistance=True)
            # if code != _code3:
            #     pass  # pro kontrolu; to by bylo divne!

            if code2 and code2 != rec.code:
                len1 = len(rec.code)
                len2 = len(code2)

                distKm = float(am.getDistanceInKm(rec.lat, rec.lon, rec2.lat, rec2.lon))
                print(f"For {rec.code} found another one: {rec2.code} {distKm: .2} km apart.")

                if distKm < 0.8:
                    if len1 < len2:    # keep the shorter ones, remove the XX-1234
                        recCodesToBeRemoved.append([rec2, rec])     # first one to be removed, second one to be kept
                        if rec2.alt != 0 and rec.alt == 0:      # if the other one does not have alt set keep it in the retained one
                            rec.alt = rec2.alt

                    elif len2 < len1:  # keep them if lengths are equal
                        recCodesToBeRemoved.append([rec, rec2])
                        if rec.alt != 0 and rec2.alt == 0:      # if the other one does not have alt set keep it in the retained one
                            rec2.alt = rec.alt

            am.xxx_return(removedRec)

    print("Codes to be removed: ")
    for recs in recCodesToBeRemoved:
        print(f"  {recs[0]} -> {recs[1]}")
        del am.airfieldsDict[recs[0].code]

    NEW_AIRFIELDS_FILE = '/tmp/00/airfieldsDEDUPLICATED.json'
    am.saveIntoFile(NEW_AIRFIELDS_FILE)

    REMOVED_CODES_FILE = '/tmp/00/removedCodes.txt'
    with open(REMOVED_CODES_FILE, 'a') as f:
        f.write('OLD;NEW\n')
        for recs in recCodesToBeRemoved:
            f.write(f"{recs[0].code};{recs[1].code}\n")

    print('KOHEU.')





