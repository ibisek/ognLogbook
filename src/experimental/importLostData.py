"""
Script to import lost data into SQL database.
Useful when there is a secondary/backup instance of logbook running while the primary did not write flights and events into db for some reason.

To export data from backup database use:
    SELECT * INTO OUTFILE "/tmp/logbook-events.sql" FROM (select * from logbook_events where ts >= 1685995200 and ts <= 1686088800);
    and
    SELECT * INTO OUTFILE "/tmp/logbook-entries.sql" FROM (select * from logbook_entries where takeoff_ts >= 1685995200 and landing_ts <= 1686088800);

Then the import is not possible due to conflicting primary keys. Hence this script needs to be used.
    -- LOAD DATA INFILE '/tmp/entries.sql' INTO TABLE logbook_entries;

-- ENTRIES FIELDS:
id, address, address_type, aircraft_type , takeoff_ts , takeoff_lat, takeoff_lon , takeoff_icao , landing_ts , landing_lat , landing_lon , landing_icao , flight_time, tow_id , flown_distance , hidden , in_ps
-- EVENTS FIELDS:
id, ts, address, address_type , aircraft_type , event , lat, lon, location_icao , flight_time , in_ps

entries.sql
events.sql

NOTE: LANDING events shall not be imported as they cause new entries to be created!!
"""

if __name__ == '__main__':

    ENTRIES_FILEPATH = '/home/ibisek/wqz/temp/entries.tsv'  # tsv = tab separated values
    EVENTS_FILEPATH = '/home/ibisek/wqz/temp/events.tsv'
    ENTRIES_OUT_FILEPATH = "/home/ibisek/wqz/temp/out-entries.sql"
    EVENTS_OUT_FILEPATH = "/home/ibisek/wqz/temp/out-events.sql"

    queries = []

    with open(ENTRIES_FILEPATH, 'r') as f:
        lines = f.readlines()

        for line in lines:
            items = line.strip().split('\t')
            items = [None if item == '\\N' else item for item in items]
            (_, address, address_type, aircraft_type, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts,
             landing_lat, landing_lon, landing_icao, flight_time, _, flown_distance, hidden, in_ps) = items

            aircraft_type = int(aircraft_type)
            takeoff_lat = float(takeoff_lat)
            takeoff_lon = float(takeoff_lon)
            takeoff_ts = int(takeoff_ts)
            takeoff_icao = f"'{takeoff_icao}'" if takeoff_icao else 'null'
            landing_lat = float(landing_lat)
            landing_lon = float(landing_lon)
            landing_ts = int(landing_ts)
            landing_icao = f"'{landing_icao}'" if landing_icao else 'null'
            flight_time = int(flight_time)
            flown_distance = int(flown_distance) if flown_distance else 'null'
            hidden = 'true' if hidden == '1' else 'false'
            in_ps = 'true' if in_ps == '1' else 'false'

            sql = f"INSERT INTO logbook_entries (address, address_type, aircraft_type, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts, landing_lat, landing_lon, landing_icao, flight_time, flown_distance, hidden, in_ps) VALUES ('{address}', '{address_type}', {aircraft_type}, {takeoff_ts}, {takeoff_lat}, {takeoff_lon}, {takeoff_icao}, {landing_ts}, {landing_lat}, {landing_lon}, {landing_icao}, {flight_time}, {flown_distance}, {hidden}, {in_ps});"
            print(sql)
            queries.append(sql)

    with open(ENTRIES_OUT_FILEPATH, 'w') as f:
        f.write('\n'.join(queries))

    queries.clear()

    with open(EVENTS_FILEPATH, 'r') as f:
        lines = f.readlines()

        for line in lines:
            items = line.strip().split('\t')
            items = [None if item == '\\N' else item for item in items]
            (_, ts, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time, in_ps) = items

            aircraft_type = int(aircraft_type)
            lat = float(lat)
            lon = float(lon)
            ts = int(ts)
            location_icao = f"'{location_icao}'" if location_icao else 'null'
            flight_time = int(flight_time)
            in_ps = 'true' if in_ps == '1' else 'false'

            sql = f"INSERT INTO logbook_events (ts, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time, in_ps) VALUES ({ts}, '{address}', '{address_type}', {aircraft_type}, '{event}', {lat}, {lon}, {location_icao}, {flight_time}, {in_ps});"
            print(sql)
            queries.append(sql)

    with open(EVENTS_OUT_FILEPATH, 'w') as f:
        f.write('\n'.join(queries))

    print("KOHEU.")

