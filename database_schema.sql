--
-- PostgreSQL database dump
--

\restrict VsywdhwRIcjCVIYQnewCrrC02UebF9OuYog0EHjmfeLaQyj4kFwWGXCME2UbUSh

-- Dumped from database version 17.7 (bdd1736)
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
-- Name: chorus_network_outage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chorus_network_outage (
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
-- Name: trademe_crawler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trademe_crawler (
    solving_start_time timestamp with time zone,
    solving_end_time timestamp with time zone,
    stop_before_page smallint,
    failed_pages integer[],
    id integer NOT NULL,
    complete_after_page smallint
);


--
-- Name: TABLE trademe_crawler; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trademe_crawler IS 'Web crawler jobs to retrieve Trademe properties.';


--
-- Name: COLUMN trademe_crawler.solving_start_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_crawler.solving_start_time IS 'Start time of web crawler job.';


--
-- Name: COLUMN trademe_crawler.solving_end_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_crawler.solving_end_time IS 'End time of web crawler job. If this field is not null, the web crawler is successfully executed.';


--
-- Name: COLUMN trademe_crawler.stop_before_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_crawler.stop_before_page IS 'Web crawler stopped (without completed) before retrieving this page.';


--
-- Name: COLUMN trademe_crawler.failed_pages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_crawler.failed_pages IS 'List of page numbers that failed to be retrieved.';


--
-- Name: COLUMN trademe_crawler.complete_after_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_crawler.complete_after_page IS 'Web crawler is successfully executed after retrieving this page.';


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

ALTER SEQUENCE public.trademe_crawler_id_seq OWNED BY public.trademe_crawler.id;


--
-- Name: trademe_properties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trademe_properties (
    listing_id character varying(16) NOT NULL,
    start_time timestamp with time zone,
    task_id integer,
    entity jsonb
);


--
-- Name: TABLE trademe_properties; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trademe_properties IS 'Auckland houses'' properties information in Trademe.';


--
-- Name: COLUMN trademe_properties.listing_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_properties.listing_id IS 'The house''s ID listed in Trademe.';


--
-- Name: COLUMN trademe_properties.start_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_properties.start_time IS 'Start time of the house listed in Trademe.';


--
-- Name: COLUMN trademe_properties.task_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trademe_properties.task_id IS 'The record is retrieved by which web crawler job. Foreign key, determined by trademe_crawler.id ';


--
-- Name: trademe_crawler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trademe_crawler ALTER COLUMN id SET DEFAULT nextval('public.trademe_crawler_id_seq'::regclass);


--
-- Name: fuel_prices fuel_prices_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_prices
    ADD CONSTRAINT fuel_prices_pk PRIMARY KEY (station_id, fuel_type, update_time);


--
-- Name: trademe_properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trademe_properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (listing_id);


--
-- Name: fuel_stations stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_stations
    ADD CONSTRAINT stations_pkey PRIMARY KEY (station_id);


--
-- Name: trademe_crawler trademe_crawler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trademe_crawler
    ADD CONSTRAINT trademe_crawler_pkey PRIMARY KEY (id);


--
-- Name: trademe_properties task_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trademe_properties
    ADD CONSTRAINT task_id FOREIGN KEY (task_id) REFERENCES public.trademe_crawler(id);


--
-- PostgreSQL database dump complete
--

\unrestrict VsywdhwRIcjCVIYQnewCrrC02UebF9OuYog0EHjmfeLaQyj4kFwWGXCME2UbUSh

