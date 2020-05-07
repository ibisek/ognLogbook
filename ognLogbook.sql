
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
    location_icao VARCHAR(4) DEFAULT 'tbd',
    --location_name VARCHAR(30)
    aircraft_registration VARCHAR(4) DEFAULT 'tbd',
    aircraft_cn VARCHAR(3)   
);

--

SELECT * FROM logbook_events;
