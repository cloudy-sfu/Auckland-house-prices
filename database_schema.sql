--
-- PostgreSQL database dump
--

\restrict 5E5mH4SnzexjTdcyM3sGg8NPsOVuMTmzZS5iqRedhnnzRNJsSiztnFLCrgf0NNW

-- Dumped from database version 17.7 (e429a59)
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
-- Name: trademe_properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trademe_properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (listing_id);


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

\unrestrict 5E5mH4SnzexjTdcyM3sGg8NPsOVuMTmzZS5iqRedhnnzRNJsSiztnFLCrgf0NNW

