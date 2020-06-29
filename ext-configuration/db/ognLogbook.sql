
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


-- (!) MYSQL ONLY (!)
--DROP TRIGGER IF EXISTS logbook_events_after_insert;
DELIMITER //
CREATE TRIGGER IF NOT EXISTS logbook_events_after_insert 
AFTER INSERT ON logbook_events FOR EACH ROW
BEGIN
IF (new.event = 'L') THEN
SELECT e.ts, e.aircraft_type, e.lat, e.lon, e.location_icao
INTO @t_ts, @t_type, @t_lat, @t_lon, @t_loc
FROM logbook_events as e 
WHERE e.address = new.address and e.event='T' and e.ts < new.ts and e.ts > (new.ts - 16*60*60)
ORDER BY e.ts DESC LIMIT 1;
INSERT INTO logbook_entries (address, aircraft_type, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts, landing_lat, landing_lon, landing_icao, flight_time) 
VALUES (new.address, @t_type, @t_ts, @t_lat, @t_lon, @t_loc, new.ts, new.lat, new.lon, new.location_icao, new.ts-@t_ts);
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
  flight_time BIGINT DEFAULT 0
);

CREATE INDEX logbook_entries_address ON logbook_entries(address);
CREATE INDEX logbook_entries_takeoff_ts ON logbook_entries(takeoff_ts);
CREATE INDEX logbook_entries_landing_ts ON logbook_entries(landing_ts);
--SHOW INDEXES FROM logbook_entries;


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


--


select * from logbook_entries as l LEFT JOIN ddb AS d ON l.address = d.device_id 
	WHERE (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL) AND (d.aircraft_cn = 'IBI')
	ORDER BY l.takeoff_ts desc;

select * from logbook_entries where takeoff_icao = 'LKKA' and aircraft_type = 1;

select * from logbook_entries where takeoff_icao = 'LKKA' and takeoff_ts between (1593332598 - 10) AND (1593332598 + 10); 
select * from logbook_events where aircraft_type IN (2,8) AND location_icao = 'LKKA' and ts between (1593332598 - 10) AND (1593332598 + 10); 

select * from logbook_entries order by landing_ts DESC limit 10; 


--alter table logbook_events add column id BIGINT PRIMARY KEY auto_increment FIRST;
--alter table logbook_entries add column id BIGINT PRIMARY KEY auto_increment FIRST;
--alter table logbook_entries add column aircraft_type TINYINT DEFAULT 0 AFTER address;


