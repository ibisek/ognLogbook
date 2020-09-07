
--create database ogn_logbook;
--grant all on ogn_logbook.* to '**'@'localhost' identified by '**';

--DROP TABLE IF EXISTS logbook_events;
CREATE TABLE logbook_events (
    id BIGINT PRIMARY KEY auto_increment,
    ts BIGINT,
    address VARCHAR(6),
    address_type TINYINT,
    aircraft_type TINYINT,
    event VARCHAR(1),
    lat DECIMAL(8,5),
    lon DECIMAL(8,5),
    location_icao VARCHAR(8) DEFAULT 'tbd',
    flight_time BIGINT DEFAULT 0
);

CREATE INDEX logbook_events_ts ON logbook_events(ts);
CREATE INDEX logbook_events_address ON logbook_events(address);
CREATE INDEX logbook_events_location_icao ON logbook_events(location_icao);
--SHOW INDEXES FROM logbook_events;


-- creation of flight entry:
-- (!) MYSQL ONLY (!)
--DROP TRIGGER IF EXISTS logbook_events_after_insert;
--DELIMITER //
--CREATE TRIGGER IF NOT EXISTS logbook_events_after_insert
--AFTER INSERT ON logbook_events FOR EACH ROW
--BEGIN
--IF (new.event = 'L') THEN
--SELECT e.ts, e.aircraft_type, e.lat, e.lon, e.location_icao
--INTO @t_ts, @t_type, @t_lat, @t_lon, @t_loc
--FROM logbook_events as e
--WHERE e.address = new.address and e.event='T' and e.ts < new.ts and e.ts > (new.ts - 16*60*60)
--ORDER BY e.ts DESC LIMIT 1;
--INSERT INTO logbook_entries (address, aircraft_type, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts, landing_lat, landing_lon, landing_icao, flight_time, tow_id)
--VALUES (new.address, @t_type, @t_ts, @t_lat, @t_lon, @t_loc, new.ts, new.lat, new.lon, new.location_icao, new.ts-@t_ts, null);
--END IF;
--END;//
--DELIMITER ;

DELIMITER //
CREATE TRIGGER IF NOT EXISTS logbook_events_after_insert 
AFTER INSERT ON logbook_events FOR EACH ROW
BEGIN
IF (new.event = 'L') THEN
CALL create_flight_entry(new.ts, new.address, new.lat, new.lon, new.location_icao);
END IF;
END;//
DELIMITER ;

--DROP TABLE IF EXISTS logbook_entries;
CREATE TABLE logbook_entries (
  id BIGINT PRIMARY KEY auto_increment,
  address VARCHAR(6),
  aircraft_type TINYINT DEFAULT 0,
  takeoff_ts BIGINT,
  takeoff_lat DECIMAL(8,5),
  takeoff_lon DECIMAL(8,5),
  takeoff_icao VARCHAR(8),
  landing_ts BIGINT,
  landing_lat DECIMAL(8,5),
  landing_lon DECIMAL(8,5),
  landing_icao VARCHAR(8),
  flight_time BIGINT DEFAULT 0,
  tow_id BIGINT references logbook_entries.id
);

CREATE INDEX logbook_entries_address ON logbook_entries(address);
CREATE INDEX logbook_entries_takeoff_ts ON logbook_entries(takeoff_ts);
CREATE INDEX logbook_entries_landing_ts ON logbook_entries(landing_ts);
CREATE INDEX logbook_entries_takeoff_icao ON logbook_entries(takeoff_icao);
CREATE INDEX logbook_entries_aircraft_type ON logbook_entries(aircraft_type);
CREATE INDEX logbook_entries_tow_id ON logbook_entries(tow_id);
--SHOW INDEXES FROM logbook_entries;

-- lookup tow plane for gliders and gliders for tug planes:
-- (!) MYSQL ONLY (!)
--DROP TRIGGER IF EXISTS logbook_entries_aerotow_lookup;
--DELIMITER //
--CREATE TRIGGER IF NOT EXISTS logbook_entries_aerotow_lookup
--AFTER INSERT ON logbook_entries FOR EACH ROW
--BEGIN
--IF (new.aircraft_type = 1 AND new.takeoff_icao IS NOT NULL) THEN	-- landing of a glider which took-off from a known airfield
--SELECT e.id INTO @t_id
--FROM logbook_entries AS e
--WHERE e.takeoff_icao = new.takeoff_icao AND e.aircraft_type IN (2,8) AND e.takeoff_ts between (new.takeoff_ts - 4) AND (new.takeoff_ts + 4) AND tow_id IS NULL
--LIMIT 1;
--IF (@t_id IS NOT NULL) THEN
--SELECT LAST_INSERT_ID() INTO @glider_entry_id;
----UPDATE logbook_entries set tow_id = @t_id where id = glider_entry_id.id;	-- update glider record
--UPDATE logbook_entries set tow_id = @glider_entry_id where id = @t_id;	-- update tow plane record
--END IF;
--END IF;
--END;//
--DELIMITER ;

--DROP TRIGGER IF EXISTS logbook_entries_aerotow_lookup_step1;
--DELIMITER //
--CREATE TRIGGER IF NOT EXISTS logbook_entries_aerotow_lookup_step1
--BEFORE INSERT ON logbook_entries FOR EACH ROW
--BEGIN
--IF (new.aircraft_type = 1 AND new.takeoff_icao IS NOT NULL) THEN	-- landing of a glider which took-off from a known airfield
--SELECT e.id INTO @t_id
--FROM logbook_entries AS e
--WHERE e.takeoff_icao = new.takeoff_icao AND e.aircraft_type IN (2,8) AND e.takeoff_ts between (new.takeoff_ts - 4) AND (new.takeoff_ts + 4) AND tow_id IS NULL
--LIMIT 1;
--IF (@t_id IS NOT NULL) THEN
--SET new.tow_id = @t_id;	-- amend glider's record
--END IF;
--END IF;
--END;//
--DELIMITER ;

--DROP TRIGGER IF EXISTS logbook_entries_aerotow_lookup_step2;
--DELIMITER //
--CREATE TRIGGER IF NOT EXISTS logbook_entries_aerotow_lookup_step2
--AFTER INSERT ON logbook_entries FOR EACH ROW
--BEGIN
--IF (new.aircraft_type = 1 AND new.takeoff_icao IS NOT NULL AND new.tow_id IS NOT NULL) THEN	-- landing of a glider which took-off from a known airfield
--SELECT LAST_INSERT_ID() INTO @glider_entry_id;
--UPDATE logbook_entries set tow_id = @glider_entry_id where id = new.tow_id;	-- update tow plane record
--END IF;
--END;//
--DELIMITER ;

-- DELETE PROCEDURE create_flight_entry;
DELIMITER //
CREATE PROCEDURE create_flight_entry (
	IN new_ts BIGINT, 
	IN new_address VARCHAR(6), 
	IN new_lat DECIMAL(8,5), 
	IN new_lon DECIMAL(8,5), 
	IN new_location_icao VARCHAR(8)
	)
BEGIN
-- create the entry:
SELECT e.ts, e.aircraft_type, e.lat, e.lon, e.location_icao
INTO @t_ts, @t_type, @t_lat, @t_lon, @t_loc
FROM logbook_events as e 
WHERE e.address = new_address and e.event='T' and e.ts < new_ts and e_ts > (new_ts - 16*60*60)
ORDER BY e.ts DESC LIMIT 1;
INSERT INTO logbook_entries (address, aircraft_type, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts, landing_lat, landing_lon, landing_icao, flight_time, tow_id) 
VALUES (new.address, @t_type, @t_ts, @t_lat, @t_lon, @t_loc, new.ts, new.lat, new.lon, new.location_icao, new.ts-@t_ts, null);
-- look up aerotow:
IF (@t_type = 1 AND @t_loc IS NOT NULL) THEN	-- landing of a glider which took-off from a known airfield
SELECT e.id INTO @tow_id
FROM logbook_entries AS e
WHERE e.takeoff_icao = @t_loc AND e.aircraft_type IN (2,8) AND e.takeoff_ts between (@t_ts - 4) AND (@t_ts + 4) AND e.tow_id IS NULL
LIMIT 1;
IF (@tow_id IS NOT NULL) THEN
SELECT LAST_INSERT_ID() INTO @glider_entry_id;
UPDATE logbook_entries set tow_id = @tow_id where id = glider_entry_id.id;	-- update glider record
UPDATE logbook_entries set tow_id = @glider_entry_id where id = @tow_id;	-- update tow plane record
END IF;
END IF;
END; //
DELIMITER ;


--DROP TABLE IF EXISTS ddb;
CREATE TABLE ddb (
	id BIGINT PRIMARY KEY auto_increment,
	device_type VARCHAR(1),
	device_id VARCHAR(6),
	aircraft_type VARCHAR(32) DEFAULT 0,
	aircraft_registration VARCHAR(8),
	aircraft_cn VARCHAR(3),
	tracked BOOL,
	identified BOOL
);

CREATE INDEX ddb_device_id ON ddb(device_id);
CREATE INDEX ddb_aircraft_registration ON ddb(aircraft_registration);
CREATE INDEX aircraft_cn ON ddb(aircraft_cn);
--SHOW INDEXES FROM ddb;

--

SELECT count(*) FROM logbook_events;

SELECT address, count(*) as n FROM logbook_events group by address order by n desc;

select * from logbook_events where address = '9792C4';

SELECT location_icao, count(*) as n FROM logbook_events group by address order by n desc;

--

SELECT l.*, d.* FROM logbook_events as l JOIN ddb as d ON l.address = d.device_id;

SELECT l.ts, l.event, l.address, l.location_icao, l.flight_time, d.aircraft_registration, d.aircraft_cn FROM logbook_events as l 
	LEFT JOIN ddb as d ON l.address = d.device_id 
	WHERE location_icao = 'LZPT'
	ORDER BY ts DESC;

--

-- LANDING TIME & LOC:
SELECT l.ts, l.address, l.location_icao, l.flight_time, d.aircraft_registration, d.aircraft_cn FROM logbook_events as l 
	JOIN ddb as d ON l.address = d.device_id 
	where l.event='L';
-- TAKE OFF TIME & LOC:
SELECT l.ts, l.address, l.location_icao FROM logbook_events as l 
	WHERE l.address = 'DDA496' and l.event='T' and l.ts < 1589289037 
	ORDER BY l.ts DESC LIMIT 1;

--

select count(id) as n , address from logbook_events group by address order by n desc;

SELECT * FROM logbook_events where address='DD8220';

--

select count(*) from ddb;

select * from logbook_entries as l LEFT JOIN ddb AS d ON l.address = d.device_id where (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL);

select * from logbook_entries where takeoff_icao='LKKA' and landing_icao like 'ED%';


select * from logbook_entries where takeoff_icao='LKKA' group by takeoff_ts order by takeoff_ts desc;

select * from logbook_events where location_icao = 'LKKA' order by ts desc;

select * from ddb;
select * from ddb where device_id = 'DDD530';


-- AEROTOW DETECTION:

select * from logbook_entries as l LEFT JOIN ddb AS d ON l.address = d.device_id 
	WHERE (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL) AND (d.aircraft_cn = 'IBI')
	ORDER BY l.takeoff_ts desc;

select * from logbook_entries where takeoff_icao = 'EHSB' and aircraft_type = 1 order by takeoff_ts desc limit 20;
select * from logbook_entries where takeoff_icao = 'LKKA' and address = '072921' order by takeoff_ts desc limit 20;
select * from logbook_entries where takeoff_icao = 'LKKA' and aircraft_type = 1 order by takeoff_ts desc limit 10;
select * from logbook_entries where takeoff_icao = 'LKKA' and aircraft_type IN (2,8) order by takeoff_ts desc limit 10;

--1599383688
--1599380316
--1599378722
-- vetron:
select * from logbook_entries where takeoff_icao = 'EHSB' and takeoff_ts between (1599497265 - 60) AND (1599497265 + 60); 
--vlekovka:
select * from logbook_events where aircraft_type IN (2,8) AND location_icao = 'LKKA' and ts between (1599378722 - 4) AND (1599378722 + 4); 
select * from logbook_entries where takeoff_icao = 'LKKA' AND aircraft_type IN (2,8) AND takeoff_ts between (1599378722 - 4) AND (1599378722 + 4) AND tow_id IS NULL; 

select * from logbook_entries where tow_id IS NOT null order by landing_ts DESC limit 10; 


--alter table logbook_events add column id BIGINT PRIMARY KEY auto_increment FIRST;
--alter table logbook_entries add column id BIGINT PRIMARY KEY auto_increment FIRST;
--alter table logbook_entries add column aircraft_type TINYINT DEFAULT 0 AFTER address;
--alter table logbook_entries add column tow_id BIGINT references logbook_entries.id;


