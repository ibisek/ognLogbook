
--create database ogn-logbook;
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
    location_icao VARCHAR(4) DEFAULT 'tbd'
    --location_name VARCHAR(30)
);

--DROP TABLE IF EXISTS ddb;
CREATE TABLE ddb (
	id BIGINT PRIMARY KEY auto_increment,
	device_type VARCHAR(1),
	device_id VARCHAR(6),
	aircraft_type VARCHAR(32),
	aircraft_registration VARCHAR(4) DEFAULT 'tbd',
	aircraft_cn VARCHAR(3),
	tracked BOOL,
	identified BOOL
);

--

SELECT count(id) FROM logbook_events;

SELECT l.*, d.* FROM logbook_events as l JOIN ddb as d ON l.address = d.device_id;

select count(id) as n , address from logbook_events group by address order by n desc;

SELECT * FROM logbook_events where address='DD8220';

