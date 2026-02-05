--
-- PostgreSQL database dump
--

\restrict E0oFsVyCXTeZuduJHXAc1hxDVEXZMPboYLY5d992s1lYs2lBEljD107AKPRpYBq

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
-- Name: fuel_prices fuel_prices_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_prices
    ADD CONSTRAINT fuel_prices_pk PRIMARY KEY (station_id, fuel_type, update_time);


--
-- Name: properties_trademe properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_trademe
    ADD CONSTRAINT properties_pkey PRIMARY KEY (listing_id);


--
-- Name: fuel_stations stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_stations
    ADD CONSTRAINT stations_pkey PRIMARY KEY (station_id);


--
-- Name: crawler_collect_trademe trademe_crawler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crawler_collect_trademe
    ADD CONSTRAINT trademe_crawler_pkey PRIMARY KEY (id);


--
-- Name: properties_trademe task_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_trademe
    ADD CONSTRAINT task_id FOREIGN KEY (task_id) REFERENCES public.crawler_collect_trademe(id);


--
-- PostgreSQL database dump complete
--

\unrestrict E0oFsVyCXTeZuduJHXAc1hxDVEXZMPboYLY5d992s1lYs2lBEljD107AKPRpYBq

