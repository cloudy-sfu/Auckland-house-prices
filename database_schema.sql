--
-- PostgreSQL database dump
--

\restrict x6yy7jyygyB63EnQXCdzJst2mVGK7pjAcDoTYyvYIzYPSTfTVPsMQTSiuvyyEMM

-- Dumped from database version 17.8 (6108b59)
-- Dumped by pg_dump version 17.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_table_access_method = heap;

--
-- Name: crawler_collect_trademe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crawler_collect_trademe (
    solving_start_time timestamp with time zone,
    solving_end_time timestamp with time zone,
    stop_before_page smallint,
    failed_pages integer[],
    id integer NOT NULL,
    complete_after_page smallint
);


--
-- Name: TABLE crawler_collect_trademe; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.crawler_collect_trademe IS 'Web crawler jobs to retrieve Trademe properties.';


--
-- Name: COLUMN crawler_collect_trademe.solving_start_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.crawler_collect_trademe.solving_start_time IS 'Start time of web crawler job.';


--
-- Name: COLUMN crawler_collect_trademe.solving_end_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.crawler_collect_trademe.solving_end_time IS 'End time of web crawler job. If this field is not null, the web crawler is successfully executed.';


--
-- Name: COLUMN crawler_collect_trademe.stop_before_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.crawler_collect_trademe.stop_before_page IS 'Web crawler stopped (without completed) before retrieving this page.';


--
-- Name: COLUMN crawler_collect_trademe.failed_pages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.crawler_collect_trademe.failed_pages IS 'List of page numbers that failed to be retrieved.';


--
-- Name: COLUMN crawler_collect_trademe.complete_after_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.crawler_collect_trademe.complete_after_page IS 'Web crawler is successfully executed after retrieving this page.';


--
-- Name: crimes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crimes (
    suburb_id integer NOT NULL,
    year smallint NOT NULL,
    month smallint NOT NULL,
    assault integer,
    burglary integer,
    endanger_people integer,
    robbery integer,
    sexual_offence integer,
    theft integer
);


--
-- Name: fuel_prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fuel_prices (
    station_id character varying(32) NOT NULL,
    fuel_type character varying(8) NOT NULL,
    brand character varying(32),
    price numeric(6,1),
    update_time timestamp with time zone NOT NULL
);


--
-- Name: TABLE fuel_prices; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.fuel_prices IS 'Records of fuel prices.';


--
-- Name: COLUMN fuel_prices.station_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_prices.station_id IS 'Same as "id" in "stations" table. Because query is based on geo_hash, which may not be unique to stations, "station_id" in this table may not be in the stations table.';


--
-- Name: COLUMN fuel_prices.fuel_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_prices.fuel_type IS 'The fuel type symbol. D - Diesel; numbers - Research Octane Number (RON).';


--
-- Name: COLUMN fuel_prices.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_prices.brand IS 'Brand of the fuel station. If missing, the station''s brand is unknown in "gaspy".';


--
-- Name: COLUMN fuel_prices.price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_prices.price IS 'Price of the fuel corresponding to "fuel_type" and uploaded at "updated_time", in unit of NZD per 100L.';


--
-- Name: COLUMN fuel_prices.update_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_prices.update_time IS 'The time that the fuel price is uploaded. It cannot be earlier than 1 days before the data is fetched.';


--
-- Name: fuel_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fuel_stations (
    station_id character varying(32) NOT NULL,
    name character varying(128),
    geo_hash character varying(8),
    latitude double precision,
    longitude double precision
);


--
-- Name: TABLE fuel_stations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.fuel_stations IS 'Information of fuel stations.';


--
-- Name: COLUMN fuel_stations.station_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_stations.station_id IS '`Original "station_key" in "gaspy", the identifier of the fuel station.';


--
-- Name: COLUMN fuel_stations.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_stations.name IS 'Name of the fuel station.';


--
-- Name: COLUMN fuel_stations.geo_hash; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fuel_stations.geo_hash IS 'Geometry hash code of quadtree, which is used by "gaspy" to search fuel stations.';


--
-- Name: internet_availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.internet_availability (
    tlc integer NOT NULL,
    service_name character varying(8),
    max_speed smallint,
    aid character varying(16),
    unit character varying(16),
    street_number character varying(32),
    street_name character varying(32),
    road_type character varying(16),
    suburb character varying(40)
);


--
-- Name: internet_outage_chorus; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.internet_outage_chorus (
    start_time timestamp with time zone,
    incident_point jsonb,
    incident_area jsonb,
    role character varying(16),
    n_impacted_services smallint,
    description character varying(64),
    update_time timestamp with time zone,
    update_text text,
    recorded_time timestamp with time zone
);


--
-- Name: macroeconomics_cpi_all; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_cpi_all (
    year smallint NOT NULL,
    quarter smallint NOT NULL,
    value double precision
);


--
-- Name: macroeconomics_cpi_non_tradable; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_cpi_non_tradable (
    year smallint NOT NULL,
    quarter smallint NOT NULL,
    value double precision
);


--
-- Name: macroeconomics_house_median_price; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_house_median_price (
    year smallint NOT NULL,
    month smallint NOT NULL,
    value integer
);


--
-- Name: macroeconomics_mortgage_rate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_mortgage_rate (
    date date NOT NULL,
    _float double precision,
    _0_5_years double precision,
    _1_years double precision,
    _1_5_years double precision,
    _2_years double precision,
    _3_years double precision,
    _4_years double precision,
    _5_years double precision
);


--
-- Name: macroeconomics_ocr; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_ocr (
    date date NOT NULL,
    value double precision
);


--
-- Name: TABLE macroeconomics_ocr; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.macroeconomics_ocr IS 'NZ official cash rates';


--
-- Name: COLUMN macroeconomics_ocr.date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.macroeconomics_ocr.date IS 'Announced date';


--
-- Name: population; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.population (
    suburb_id integer NOT NULL,
    year smallint NOT NULL,
    value integer
);


--
-- Name: properties_homes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_homes (
    property_id uuid NOT NULL,
    suburb_id integer,
    latitude double precision,
    longitude double precision,
    decade_built smallint,
    has_deck boolean,
    has_laundry boolean,
    has_gas boolean,
    bathrooms smallint,
    bedrooms smallint,
    garage_parking smallint,
    car_spaces smallint,
    record_of_title character varying(16)[],
    ownership_type character varying(32),
    external_wall_material character varying(1),
    roof_material character varying(1),
    contour character varying(2),
    estimated_price integer,
    search_time_utc timestamp with time zone DEFAULT now(),
    trademe_listing_id character varying(16)[],
    address character varying(128)
);


--
-- Name: properties_homes_detail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_homes_detail (
    property_id uuid NOT NULL,
    sales jsonb,
    capital_values jsonb,
    external_wall_condition character varying(1),
    roof_condition character varying(1),
    estimated_rental_lb integer,
    estimated_rental_ub integer,
    estimated_rental_date date,
    estimated_price_date date
);


--
-- Name: properties_homes_internet_availability_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_homes_internet_availability_link (
    property_id uuid NOT NULL,
    tlc integer
);


--
-- Name: properties_homes_land_tax_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_homes_land_tax_link (
    property_id uuid NOT NULL,
    assessment_id character varying(16)
);


--
-- Name: properties_land_tax; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_land_tax (
    assessment_id character varying(16) NOT NULL,
    land_area integer,
    floor_area integer,
    building_coverage_area integer,
    land_value integer,
    improvements_value integer,
    land_tax double precision,
    land_usage character varying(64),
    land_tax_break_down jsonb,
    nztm2000_x double precision,
    nztm2000_y double precision,
    record_of_title character varying(16)[],
    street_number character varying(32),
    street_name character varying(32),
    suburb_name character varying(32)
);


--
-- Name: COLUMN properties_land_tax.assessment_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.properties_land_tax.assessment_id IS 'Auckland council rate account key';


--
-- Name: properties_state_houses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_state_houses (
    parcel_id integer NOT NULL,
    record_of_title character varying(16),
    owner character varying(64),
    area double precision,
    updated_date date,
    geometry jsonb
);


--
-- Name: properties_state_houses_new_dev; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_state_houses_new_dev (
    info_marker_id integer NOT NULL,
    local_board character varying(64),
    address character varying(256),
    updated_time character varying(32),
    land_area integer,
    build_type character varying(256),
    number_of_homes character varying(64),
    parking_space character varying(32),
    progress character varying(32),
    planned_completion character varying(32),
    location jsonb,
    step character varying(32)
);


--
-- Name: properties_trademe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_trademe (
    listing_id character varying(16) NOT NULL,
    start_time timestamp with time zone,
    task_id integer,
    entity jsonb
);


--
-- Name: COLUMN properties_trademe.listing_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.properties_trademe.listing_id IS 'The house''s ID listed in Trademe.';


--
-- Name: COLUMN properties_trademe.start_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.properties_trademe.start_time IS 'Start time of the house listed in Trademe.';


--
-- Name: COLUMN properties_trademe.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.properties_trademe.task_id IS 'The record is retrieved by which web crawler job. Foreign key, determined by trademe_crawler.id ';


--
-- Name: schools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schools (
    school_number smallint NOT NULL,
    school_name character varying(128),
    street character varying(64),
    suburb character varying(32),
    city character varying(32),
    school_type character varying(64),
    gender character varying(8),
    enrollment_scheme boolean,
    latitude double precision,
    longitude double precision,
    students_total smallint,
    students_european smallint,
    students_maori smallint,
    students_pacific smallint,
    students_asian smallint,
    students_melaa smallint,
    students_others smallint,
    students_international smallint,
    boarding_facilities boolean,
    year_from smallint,
    year_to smallint,
    is_public boolean,
    eqi smallint,
    lang_eng boolean,
    lang_maori boolean,
    lang_pacific boolean,
    open_date date
);


--
-- Name: TABLE schools; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.schools IS 'https://www.educationcounts.govt.nz/directories/list-of-nz-schools';


--
-- Name: COLUMN schools.enrollment_scheme; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.schools.enrollment_scheme IS 'If True, students in the zone are guaranteed admitted; others can apply.';


--
-- Name: COLUMN schools.students_melaa; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.schools.students_melaa IS 'Middle Eastern, Latin American, African';


--
-- Name: COLUMN schools.lang_eng; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.schools.lang_eng IS 'Some students are taught in English.';


--
-- Name: COLUMN schools.lang_maori; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.schools.lang_maori IS 'Some students are taught in Maori.';


--
-- Name: COLUMN schools.lang_pacific; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.schools.lang_pacific IS 'Some students are tanght in Pacific language.';


--
-- Name: suburbs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suburbs (
    suburb_id integer NOT NULL,
    name character varying(32),
    geometry jsonb
);


--
-- Name: trademe_crawler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trademe_crawler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trademe_crawler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trademe_crawler_id_seq OWNED BY public.crawler_collect_trademe.id;


--
-- Name: crawler_collect_trademe id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crawler_collect_trademe ALTER COLUMN id SET DEFAULT nextval('public.trademe_crawler_id_seq'::regclass);


--
-- Name: crimes crimes_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crimes
    ADD CONSTRAINT crimes_pk PRIMARY KEY (suburb_id, year, month);


--
-- Name: fuel_prices fuel_prices_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_prices
    ADD CONSTRAINT fuel_prices_pk PRIMARY KEY (station_id, fuel_type, update_time);


--
-- Name: internet_availability internet_availability_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.internet_availability
    ADD CONSTRAINT internet_availability_pk PRIMARY KEY (tlc);


--
-- Name: macroeconomics_cpi_all macroeconomics_cpi_all_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_cpi_all
    ADD CONSTRAINT macroeconomics_cpi_all_pk PRIMARY KEY (year, quarter);


--
-- Name: macroeconomics_cpi_non_tradable macroeconomics_cpi_non_tradable_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_cpi_non_tradable
    ADD CONSTRAINT macroeconomics_cpi_non_tradable_pk PRIMARY KEY (year, quarter);


--
-- Name: macroeconomics_house_median_price macroeconomics_house_median_price_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_house_median_price
    ADD CONSTRAINT macroeconomics_house_median_price_pk PRIMARY KEY (year, month);


--
-- Name: macroeconomics_mortgage_rate macroeconomics_mortgage_rate_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_mortgage_rate
    ADD CONSTRAINT macroeconomics_mortgage_rate_pk PRIMARY KEY (date);


--
-- Name: macroeconomics_ocr macroeconomics_ocr_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_ocr
    ADD CONSTRAINT macroeconomics_ocr_pk PRIMARY KEY (date);


--
-- Name: population population_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.population
    ADD CONSTRAINT population_pk PRIMARY KEY (suburb_id, year);


--
-- Name: properties_homes_internet_availability_link properties_homes_internet_availability_link_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_homes_internet_availability_link
    ADD CONSTRAINT properties_homes_internet_availability_link_pk PRIMARY KEY (property_id);


--
-- Name: properties_homes_land_tax_link properties_homes_land_tax_link_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_homes_land_tax_link
    ADD CONSTRAINT properties_homes_land_tax_link_pk PRIMARY KEY (property_id);


--
-- Name: properties_homes properties_homes_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_homes
    ADD CONSTRAINT properties_homes_pk PRIMARY KEY (property_id);


--
-- Name: properties_land_tax properties_land_tax_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_land_tax
    ADD CONSTRAINT properties_land_tax_pk PRIMARY KEY (assessment_id);


--
-- Name: properties_trademe properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_trademe
    ADD CONSTRAINT properties_pkey PRIMARY KEY (listing_id);


--
-- Name: properties_state_houses_new_dev properties_state_houses_new_dev_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_state_houses_new_dev
    ADD CONSTRAINT properties_state_houses_new_dev_pk PRIMARY KEY (info_marker_id);


--
-- Name: properties_state_houses properties_state_houses_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_state_houses
    ADD CONSTRAINT properties_state_houses_pk PRIMARY KEY (parcel_id);


--
-- Name: properties_homes_detail property_homes_detail_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_homes_detail
    ADD CONSTRAINT property_homes_detail_pk PRIMARY KEY (property_id);


--
-- Name: schools schools_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schools
    ADD CONSTRAINT schools_pk PRIMARY KEY (school_number);


--
-- Name: fuel_stations stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_stations
    ADD CONSTRAINT stations_pkey PRIMARY KEY (station_id);


--
-- Name: suburbs suburbs_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suburbs
    ADD CONSTRAINT suburbs_pk PRIMARY KEY (suburb_id);


--
-- Name: crawler_collect_trademe trademe_crawler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crawler_collect_trademe
    ADD CONSTRAINT trademe_crawler_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict x6yy7jyygyB63EnQXCdzJst2mVGK7pjAcDoTYyvYIzYPSTfTVPsMQTSiuvyyEMM

