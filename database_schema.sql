--
-- PostgreSQL database dump
--

\restrict fpEvjA2aS15Kgs6nz12fpYgbGXiUTd9OzIfGcOiYK8vz47bZnfJ32cRRVyoBh61

-- Dumped from database version 17.8 (a48d9ca)
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

--
-- Name: neon_auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA neon_auth;


SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.account (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "accountId" text NOT NULL,
    "providerId" text NOT NULL,
    "userId" uuid NOT NULL,
    "accessToken" text,
    "refreshToken" text,
    "idToken" text,
    "accessTokenExpiresAt" timestamp with time zone,
    "refreshTokenExpiresAt" timestamp with time zone,
    scope text,
    password text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL
);


--
-- Name: invitation; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.invitation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    email text NOT NULL,
    role text,
    status text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "inviterId" uuid NOT NULL
);


--
-- Name: jwks; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.jwks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "publicKey" text NOT NULL,
    "privateKey" text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL,
    "expiresAt" timestamp with time zone
);


--
-- Name: member; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.member (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    "userId" uuid NOT NULL,
    role text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL
);


--
-- Name: organization; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.organization (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    logo text,
    "createdAt" timestamp with time zone NOT NULL,
    metadata text
);


--
-- Name: project_config; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.project_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    endpoint_id text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    trusted_origins jsonb NOT NULL,
    social_providers jsonb NOT NULL,
    email_provider jsonb,
    email_and_password jsonb,
    allow_localhost boolean NOT NULL,
    plugin_configs jsonb,
    webhook_config jsonb
);


--
-- Name: session; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.session (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    token text NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL,
    "ipAddress" text,
    "userAgent" text,
    "userId" uuid NOT NULL,
    "impersonatedBy" text,
    "activeOrganizationId" text
);


--
-- Name: user; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth."user" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    email text NOT NULL,
    "emailVerified" boolean NOT NULL,
    image text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    role text,
    banned boolean,
    "banReason" text,
    "banExpires" timestamp with time zone
);


--
-- Name: verification; Type: TABLE; Schema: neon_auth; Owner: -
--

CREATE TABLE neon_auth.verification (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    identifier text NOT NULL,
    value text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: age_structure; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.age_structure (
    suburb_id integer NOT NULL,
    year smallint NOT NULL,
    age_group smallint NOT NULL,
    percentage double precision
);


--
-- Name: broadband_availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_availability (
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
-- Name: broadband_coverage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_coverage (
    x integer NOT NULL,
    y integer NOT NULL,
    geometry jsonb
);


--
-- Name: broadband_coverage_hyperfiber; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_coverage_hyperfiber (
    geometry jsonb,
    y integer NOT NULL,
    x integer NOT NULL
);


--
-- Name: broadband_coverage_tree; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_coverage_tree (
    z smallint NOT NULL,
    x integer NOT NULL,
    y integer NOT NULL,
    q1_empty boolean,
    q1_full boolean,
    q2_empty boolean,
    q2_full boolean,
    q3_empty boolean,
    q3_full boolean,
    q4_empty boolean,
    q4_full boolean,
    role smallint,
    parent_x integer,
    parent_y integer
);


--
-- Name: COLUMN broadband_coverage_tree.x; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.broadband_coverage_tree.x IS 'smallint supports max to zoom=15';


--
-- Name: COLUMN broadband_coverage_tree.y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.broadband_coverage_tree.y IS 'smallint supports max to zoom=15';


--
-- Name: broadband_coverage_tree_hyperfiber; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_coverage_tree_hyperfiber (
    q3_empty boolean,
    q2_empty boolean,
    q2_full boolean,
    x integer NOT NULL,
    q1_full boolean,
    z smallint NOT NULL,
    q3_full boolean,
    y integer NOT NULL,
    q4_empty boolean,
    role smallint,
    q4_full boolean,
    parent_y integer,
    q1_empty boolean,
    parent_x integer
);


--
-- Name: COLUMN broadband_coverage_tree_hyperfiber.x; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.broadband_coverage_tree_hyperfiber.x IS 'smallint supports max to zoom=15';


--
-- Name: COLUMN broadband_coverage_tree_hyperfiber.y; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.broadband_coverage_tree_hyperfiber.y IS 'smallint supports max to zoom=15';


--
-- Name: broadband_outage_chorus; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.broadband_outage_chorus (
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
-- Name: collect_auction_interest; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collect_auction_interest (
    id integer NOT NULL,
    solving_start_time timestamp with time zone DEFAULT now(),
    solving_end_time timestamp with time zone,
    stop_before_page smallint,
    failed_pages smallint[],
    complete_after_page smallint
);


--
-- Name: collect_auction_interest_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.collect_auction_interest_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: collect_auction_interest_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.collect_auction_interest_id_seq OWNED BY public.collect_auction_interest.id;


--
-- Name: collect_trademe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collect_trademe (
    solving_start_time timestamp with time zone DEFAULT now(),
    solving_end_time timestamp with time zone,
    stop_before_page smallint,
    failed_pages smallint[],
    id integer NOT NULL,
    complete_after_page smallint
);


--
-- Name: TABLE collect_trademe; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.collect_trademe IS 'Web crawler jobs to retrieve Trademe properties.';


--
-- Name: COLUMN collect_trademe.solving_start_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.collect_trademe.solving_start_time IS 'Start time of web crawler job.';


--
-- Name: COLUMN collect_trademe.solving_end_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.collect_trademe.solving_end_time IS 'End time of web crawler job. If this field is not null, the web crawler is successfully executed.';


--
-- Name: COLUMN collect_trademe.stop_before_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.collect_trademe.stop_before_page IS 'Web crawler stopped (without completed) before retrieving this page.';


--
-- Name: COLUMN collect_trademe.failed_pages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.collect_trademe.failed_pages IS 'List of page numbers that failed to be retrieved.';


--
-- Name: COLUMN collect_trademe.complete_after_page; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.collect_trademe.complete_after_page IS 'Web crawler is successfully executed after retrieving this page.';


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
-- Name: ethnicity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ethnicity (
    suburb_id integer NOT NULL,
    year smallint NOT NULL,
    ethnicity character varying(32) NOT NULL,
    percentage double precision
);


--
-- Name: flood_coastal_inundation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flood_coastal_inundation (
    object_id integer NOT NULL,
    geometry jsonb
);


--
-- Name: flood_flood_plains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flood_flood_plains (
    sde_object_id integer NOT NULL,
    year_produced smallint,
    area double precision,
    geometry jsonb,
    published_date date
);


--
-- Name: flood_flood_prone_areas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flood_flood_prone_areas (
    fpa_id integer NOT NULL,
    catchment_area integer,
    pounding_depth_100yr double precision,
    pounding_depth_spill double precision,
    lowest_ground_elevation double precision,
    rainfall_100yr smallint,
    rainfall_spill smallint,
    runoff_volume integer,
    capacity_volume integer,
    area double precision,
    geometry jsonb
);


--
-- Name: flood_overland_flow_paths; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flood_overland_flow_paths (
    global_id uuid NOT NULL,
    catchment_contributing_area smallint,
    geometry jsonb
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
-- Name: macroeconomics_wholesale_swap_rate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macroeconomics_wholesale_swap_rate (
    date date NOT NULL,
    _1_years double precision,
    _2_years double precision,
    _3_years double precision,
    _4_years double precision,
    _5_years double precision,
    _7_years double precision,
    _10_years double precision
);


--
-- Name: population; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.population (
    suburb_id integer NOT NULL,
    year smallint NOT NULL,
    value integer
);


--
-- Name: properties_auction_interest; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_auction_interest (
    bedroom smallint,
    bathroom smallint,
    parking smallint,
    address character varying(128) NOT NULL,
    sold boolean,
    price integer,
    status character varying(16),
    qv_estimation integer,
    agents character varying(32)[],
    auction_date date NOT NULL,
    agency character varying(32),
    task_id integer
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
-- Name: properties_homes_broadband_availability_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties_homes_broadband_availability_link (
    property_id uuid NOT NULL,
    tlc integer
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
-- Name: schools_zones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schools_zones (
    school_number smallint NOT NULL,
    geometry jsonb,
    poly_id integer NOT NULL
);


--
-- Name: state_houses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.state_houses (
    parcel_id integer NOT NULL,
    record_of_title character varying(16),
    owner character varying(64),
    area double precision,
    updated_date date,
    geometry jsonb
);


--
-- Name: state_houses_new_dev; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.state_houses_new_dev (
    info_marker_id integer NOT NULL,
    local_board character varying(64),
    address character varying(256),
    land_area integer,
    build_type character varying(256),
    number_of_homes character varying(64),
    parking_space character varying(32),
    progress character varying(32),
    planned_completion character varying(32),
    location jsonb,
    step character varying(32),
    updated_year smallint,
    updated_month smallint
);


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

ALTER SEQUENCE public.trademe_crawler_id_seq OWNED BY public.collect_trademe.id;


--
-- Name: collect_auction_interest id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collect_auction_interest ALTER COLUMN id SET DEFAULT nextval('public.collect_auction_interest_id_seq'::regclass);


--
-- Name: collect_trademe id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collect_trademe ALTER COLUMN id SET DEFAULT nextval('public.trademe_crawler_id_seq'::regclass);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: invitation invitation_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT invitation_pkey PRIMARY KEY (id);


--
-- Name: jwks jwks_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.jwks
    ADD CONSTRAINT jwks_pkey PRIMARY KEY (id);


--
-- Name: member member_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT member_pkey PRIMARY KEY (id);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (id);


--
-- Name: organization organization_slug_key; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_slug_key UNIQUE (slug);


--
-- Name: project_config project_config_endpoint_id_key; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_endpoint_id_key UNIQUE (endpoint_id);


--
-- Name: project_config project_config_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_pkey PRIMARY KEY (id);


--
-- Name: session session_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);


--
-- Name: session session_token_key; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_token_key UNIQUE (token);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: verification verification_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.verification
    ADD CONSTRAINT verification_pkey PRIMARY KEY (id);


--
-- Name: age_structure age_structure_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.age_structure
    ADD CONSTRAINT age_structure_pk PRIMARY KEY (suburb_id, year, age_group);


--
-- Name: broadband_availability broadband_availability_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.broadband_availability
    ADD CONSTRAINT broadband_availability_pk PRIMARY KEY (tlc);


--
-- Name: broadband_coverage_hyperfiber broadband_coverage_hyperfiber_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.broadband_coverage_hyperfiber
    ADD CONSTRAINT broadband_coverage_hyperfiber_pk PRIMARY KEY (x, y);


--
-- Name: broadband_coverage broadband_coverage_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.broadband_coverage
    ADD CONSTRAINT broadband_coverage_pk PRIMARY KEY (x, y);


--
-- Name: broadband_coverage_tree_hyperfiber broadband_coverage_tree_hyperfiber_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.broadband_coverage_tree_hyperfiber
    ADD CONSTRAINT broadband_coverage_tree_hyperfiber_pk PRIMARY KEY (z, x, y);


--
-- Name: broadband_coverage_tree broadband_coverage_tree_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.broadband_coverage_tree
    ADD CONSTRAINT broadband_coverage_tree_pk PRIMARY KEY (z, x, y);


--
-- Name: collect_auction_interest collect_auction_interest_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collect_auction_interest
    ADD CONSTRAINT collect_auction_interest_pk PRIMARY KEY (id);


--
-- Name: crimes crimes_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crimes
    ADD CONSTRAINT crimes_pk PRIMARY KEY (suburb_id, year, month);


--
-- Name: ethnicity ethnicity_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ethnicity
    ADD CONSTRAINT ethnicity_pk PRIMARY KEY (suburb_id, year, ethnicity);


--
-- Name: flood_coastal_inundation flood_coastal_inundation_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flood_coastal_inundation
    ADD CONSTRAINT flood_coastal_inundation_pk PRIMARY KEY (object_id);


--
-- Name: flood_flood_plains flood_flood_plains_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flood_flood_plains
    ADD CONSTRAINT flood_flood_plains_pk PRIMARY KEY (sde_object_id);


--
-- Name: flood_flood_prone_areas flood_flood_prone_areas_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flood_flood_prone_areas
    ADD CONSTRAINT flood_flood_prone_areas_pk PRIMARY KEY (fpa_id);


--
-- Name: flood_overland_flow_paths flood_overland_flow_paths_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flood_overland_flow_paths
    ADD CONSTRAINT flood_overland_flow_paths_pk PRIMARY KEY (global_id);


--
-- Name: fuel_prices fuel_prices_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fuel_prices
    ADD CONSTRAINT fuel_prices_pk PRIMARY KEY (station_id, fuel_type, update_time);


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
-- Name: macroeconomics_wholesale_swap_rate macroeconomics_wholesale_swap_rate_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macroeconomics_wholesale_swap_rate
    ADD CONSTRAINT macroeconomics_wholesale_swap_rate_pk PRIMARY KEY (date);


--
-- Name: population population_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.population
    ADD CONSTRAINT population_pk PRIMARY KEY (suburb_id, year);


--
-- Name: properties_auction_interest properties_auction_interest_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_auction_interest
    ADD CONSTRAINT properties_auction_interest_pk PRIMARY KEY (auction_date, address);


--
-- Name: properties_homes_broadband_availability_link properties_homes_broadband_availability_link_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_homes_broadband_availability_link
    ADD CONSTRAINT properties_homes_broadband_availability_link_pk PRIMARY KEY (property_id);


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
-- Name: schools_zones schools_zones_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schools_zones
    ADD CONSTRAINT schools_zones_pk PRIMARY KEY (school_number, poly_id);


--
-- Name: state_houses_new_dev state_houses_new_dev_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.state_houses_new_dev
    ADD CONSTRAINT state_houses_new_dev_pk PRIMARY KEY (info_marker_id);


--
-- Name: state_houses state_houses_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.state_houses
    ADD CONSTRAINT state_houses_pk PRIMARY KEY (parcel_id);


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
-- Name: collect_trademe trademe_crawler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collect_trademe
    ADD CONSTRAINT trademe_crawler_pkey PRIMARY KEY (id);


--
-- Name: account_userId_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX "account_userId_idx" ON neon_auth.account USING btree ("userId");


--
-- Name: invitation_email_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX invitation_email_idx ON neon_auth.invitation USING btree (email);


--
-- Name: invitation_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX "invitation_organizationId_idx" ON neon_auth.invitation USING btree ("organizationId");


--
-- Name: member_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX "member_organizationId_idx" ON neon_auth.member USING btree ("organizationId");


--
-- Name: member_userId_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX "member_userId_idx" ON neon_auth.member USING btree ("userId");


--
-- Name: organization_slug_uidx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE UNIQUE INDEX organization_slug_uidx ON neon_auth.organization USING btree (slug);


--
-- Name: session_userId_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX "session_userId_idx" ON neon_auth.session USING btree ("userId");


--
-- Name: verification_identifier_idx; Type: INDEX; Schema: neon_auth; Owner: -
--

CREATE INDEX verification_identifier_idx ON neon_auth.verification USING btree (identifier);


--
-- Name: account account_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT "account_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_inviterId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_inviterId_fkey" FOREIGN KEY ("inviterId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: session session_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: -
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT "session_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: properties_auction_interest properties_auction_interest_collect_auction_interest_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_auction_interest
    ADD CONSTRAINT properties_auction_interest_collect_auction_interest_id_fk FOREIGN KEY (task_id) REFERENCES public.collect_auction_interest(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: properties_trademe properties_trademe_collect_trademe_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties_trademe
    ADD CONSTRAINT properties_trademe_collect_trademe_id_fk FOREIGN KEY (task_id) REFERENCES public.collect_trademe(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict fpEvjA2aS15Kgs6nz12fpYgbGXiUTd9OzIfGcOiYK8vz47bZnfJ32cRRVyoBh61

