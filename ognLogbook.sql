
--create database ogn_logbook;
--grant all on ogn_logbook.* to '**'@'localhost' identified by '**';

--DROP TABLE IF EXISTS logbook_events;
CREATE TABLE logbook_events (
	--id BIGINT PRIMARY KEY auto_increment,
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

CREATE INDEX logbook_events_address ON logbook_events(address);
CREATE INDEX logbook_events_location_icao ON logbook_events(location_icao);
--SHOW INDEXES FROM logbook_events;


-- (!) MYSQL ONLY (!)
DELIMITER //
CREATE TRIGGER IF NOT EXISTS logbook_events_after_insert 
AFTER INSERT ON logbook_events FOR EACH ROW
BEGIN
IF (new.event = 'L') THEN
SELECT e.ts , e.lat, e.lon, e.location_icao
INTO @t_ts, @t_lat, @t_lon, @t_loc
FROM logbook_events as e 
WHERE e.address = new.address and e.event='T' and e.ts < new.ts 
ORDER BY e.ts DESC LIMIT 1;
INSERT INTO logbook_entries (address, takeoff_ts, takeoff_lat, takeoff_lon, takeoff_icao, landing_ts, landing_lat, landing_lon, landing_icao, flight_time) 
VALUES (new.address, @t_ts, @t_lat, @t_lon, @t_loc, new.ts, new.lat, new.lon, new.location_icao, new.flight_time);
END IF;
END;//
DELIMITER ;


--DROP TABLE IF EXISTS logbook_entries;
CREATE TABLE logbook_entries (
  address VARCHAR(6),
  takeoff_ts BIGINT,
  takeoff_lat DECIMAL(8,5),
  takeoff_lon DECIMAL(8,5),
  takeoff_icao VARCHAR(4),
  landing_ts BIGINT,
  landing_lat DECIMAL(8,5),
  landing_lon DECIMAL(8,5),
  landing_icao VARCHAR(4),
  flight_time BIGINT DEFAULT 0
);

--DROP TABLE IF EXISTS ddb;
CREATE TABLE ddb (
	--id BIGINT PRIMARY KEY auto_increment,
	device_type VARCHAR(1),
	device_id VARCHAR(6),
	aircraft_type VARCHAR(32),
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

