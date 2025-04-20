--
-- PostgreSQL database dump
--

-- Dumped from database version 17.3 (Debian 17.3-3.pgdg120+1)
-- Dumped by pg_dump version 17.3 (Debian 17.3-3.pgdg120+1)

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
-- Name: gym; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA gym;


ALTER SCHEMA gym OWNER TO postgres;

--
-- Name: nutrition; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA nutrition;


ALTER SCHEMA nutrition OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ejercicios; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.ejercicios (
    id integer NOT NULL,
    fecha timestamp without time zone,
    ejercicio character varying(255),
    repeticiones jsonb,
    duracion integer,
    user_id character varying(255),
    user_uuid integer
);


ALTER TABLE gym.ejercicios OWNER TO postgres;

--
-- Name: ejercicios_id_seq; Type: SEQUENCE; Schema: gym; Owner: postgres
--

CREATE SEQUENCE gym.ejercicios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gym.ejercicios_id_seq OWNER TO postgres;

--
-- Name: ejercicios_id_seq; Type: SEQUENCE OWNED BY; Schema: gym; Owner: postgres
--

ALTER SEQUENCE gym.ejercicios_id_seq OWNED BY gym.ejercicios.id;


--
-- Name: fitbit_auth_temp; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.fitbit_auth_temp (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    client_id character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE gym.fitbit_auth_temp OWNER TO postgres;

--
-- Name: fitbit_auth_temp_id_seq; Type: SEQUENCE; Schema: gym; Owner: postgres
--

CREATE SEQUENCE gym.fitbit_auth_temp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gym.fitbit_auth_temp_id_seq OWNER TO postgres;

--
-- Name: fitbit_auth_temp_id_seq; Type: SEQUENCE OWNED BY; Schema: gym; Owner: postgres
--

ALTER SEQUENCE gym.fitbit_auth_temp_id_seq OWNED BY gym.fitbit_auth_temp.id;


--
-- Name: fitbit_tokens; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.fitbit_tokens (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    user_uuid integer,
    client_id character varying(255) NOT NULL,
    access_token text NOT NULL,
    refresh_token text NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE gym.fitbit_tokens OWNER TO postgres;

--
-- Name: fitbit_tokens_id_seq; Type: SEQUENCE; Schema: gym; Owner: postgres
--

CREATE SEQUENCE gym.fitbit_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gym.fitbit_tokens_id_seq OWNER TO postgres;

--
-- Name: fitbit_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: gym; Owner: postgres
--

ALTER SEQUENCE gym.fitbit_tokens_id_seq OWNED BY gym.fitbit_tokens.id;


--
-- Name: link_codes; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.link_codes (
    code character varying(10) NOT NULL,
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone,
    used boolean DEFAULT false
);


ALTER TABLE gym.link_codes OWNER TO postgres;

--
-- Name: rutinas; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.rutinas (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    user_uuid integer,
    dia_semana integer NOT NULL,
    ejercicios jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rutinas_dia_semana_check CHECK (((dia_semana >= 1) AND (dia_semana <= 7)))
);


ALTER TABLE gym.rutinas OWNER TO postgres;

--
-- Name: rutinas_id_seq; Type: SEQUENCE; Schema: gym; Owner: postgres
--

CREATE SEQUENCE gym.rutinas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gym.rutinas_id_seq OWNER TO postgres;

--
-- Name: rutinas_id_seq; Type: SEQUENCE OWNED BY; Schema: gym; Owner: postgres
--

ALTER SEQUENCE gym.rutinas_id_seq OWNED BY gym.rutinas.id;


--
-- Name: users; Type: TABLE; Schema: gym; Owner: postgres
--

CREATE TABLE gym.users (
    id integer NOT NULL,
    telegram_id character varying(255),
    google_id character varying(255),
    email character varying(255),
    display_name character varying(255),
    profile_picture character varying(512),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE gym.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: gym; Owner: postgres
--

CREATE SEQUENCE gym.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gym.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: gym; Owner: postgres
--

ALTER SEQUENCE gym.users_id_seq OWNED BY gym.users.id;


--
-- Name: daily_tracking; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.daily_tracking (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    tracking_date date NOT NULL,
    completed_meals jsonb,
    calorie_note text,
    actual_calories integer,
    excess_deficit integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE nutrition.daily_tracking OWNER TO postgres;

--
-- Name: daily_tracking_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.daily_tracking_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.daily_tracking_id_seq OWNER TO postgres;

--
-- Name: daily_tracking_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.daily_tracking_id_seq OWNED BY nutrition.daily_tracking.id;


--
-- Name: ingredients; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.ingredients (
    id integer NOT NULL,
    ingredient_name character varying(255) NOT NULL,
    calories integer NOT NULL,
    proteins numeric(10,2) NOT NULL,
    carbohydrates numeric(10,2) NOT NULL,
    fats numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_base boolean DEFAULT false
);


ALTER TABLE nutrition.ingredients OWNER TO postgres;

--
-- Name: ingredients_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.ingredients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.ingredients_id_seq OWNER TO postgres;

--
-- Name: ingredients_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.ingredients_id_seq OWNED BY nutrition.ingredients.id;


--
-- Name: meal_ingredients; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.meal_ingredients (
    id integer NOT NULL,
    meal_id integer NOT NULL,
    ingredient_id integer NOT NULL,
    quantity numeric(10,2) DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE nutrition.meal_ingredients OWNER TO postgres;

--
-- Name: meal_ingredients_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.meal_ingredients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.meal_ingredients_id_seq OWNER TO postgres;

--
-- Name: meal_ingredients_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.meal_ingredients_id_seq OWNED BY nutrition.meal_ingredients.id;


--
-- Name: meal_plan_items; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.meal_plan_items (
    id integer NOT NULL,
    meal_plan_id integer,
    meal_id integer,
    day_of_week integer,
    meal_type character varying(50),
    quantity numeric(10,2) DEFAULT 1.0,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    plan_date date,
    unit character varying(20) DEFAULT 'g'::character varying
);


ALTER TABLE nutrition.meal_plan_items OWNER TO postgres;

--
-- Name: meal_plan_items_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.meal_plan_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.meal_plan_items_id_seq OWNER TO postgres;

--
-- Name: meal_plan_items_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.meal_plan_items_id_seq OWNED BY nutrition.meal_plan_items.id;


--
-- Name: meal_plans; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.meal_plans (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    plan_name character varying(255) NOT NULL,
    start_date date,
    end_date date,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    target_calories integer,
    target_protein_g numeric(10,2) DEFAULT NULL::numeric,
    target_carbs_g numeric(10,2) DEFAULT NULL::numeric,
    target_fat_g numeric(10,2) DEFAULT NULL::numeric,
    goal character varying(50) DEFAULT NULL::character varying,
    CONSTRAINT meal_plans_target_calories_check CHECK (((target_calories IS NULL) OR (target_calories >= 0))),
    CONSTRAINT meal_plans_target_carbs_g_check CHECK (((target_carbs_g IS NULL) OR (target_carbs_g >= (0)::numeric))),
    CONSTRAINT meal_plans_target_fat_g_check CHECK (((target_fat_g IS NULL) OR (target_fat_g >= (0)::numeric))),
    CONSTRAINT meal_plans_target_protein_g_check CHECK (((target_protein_g IS NULL) OR (target_protein_g >= (0)::numeric)))
);


ALTER TABLE nutrition.meal_plans OWNER TO postgres;

--
-- Name: meal_plans_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.meal_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.meal_plans_id_seq OWNER TO postgres;

--
-- Name: meal_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.meal_plans_id_seq OWNED BY nutrition.meal_plans.id;


--
-- Name: meals; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.meals (
    id integer NOT NULL,
    meal_name character varying(255) NOT NULL,
    recipe text,
    ingredients text,
    calories numeric(10,2) NOT NULL,
    proteins numeric(10,2) NOT NULL,
    carbohydrates numeric(10,2) NOT NULL,
    fats numeric(10,2) NOT NULL,
    image_url character varying(512),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE nutrition.meals OWNER TO postgres;

--
-- Name: meals_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.meals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.meals_id_seq OWNER TO postgres;

--
-- Name: meals_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.meals_id_seq OWNED BY nutrition.meals.id;


--
-- Name: user_nutrition_profiles; Type: TABLE; Schema: nutrition; Owner: postgres
--

CREATE TABLE nutrition.user_nutrition_profiles (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    sex character varying(10) NOT NULL,
    age integer NOT NULL,
    height integer NOT NULL,
    weight numeric(10,2) NOT NULL,
    body_fat_percentage numeric(5,2),
    activity_level character varying(50) NOT NULL,
    goal character varying(50) NOT NULL,
    bmr numeric(10,2) NOT NULL,
    bmi numeric(5,2) NOT NULL,
    daily_calories numeric(10,2) NOT NULL,
    proteins_grams numeric(10,2) NOT NULL,
    carbs_grams numeric(10,2) NOT NULL,
    fats_grams numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    formula character varying(50),
    goal_intensity character varying(50),
    units character varying(10),
    tdee numeric(10,2)
);


ALTER TABLE nutrition.user_nutrition_profiles OWNER TO postgres;

--
-- Name: user_nutrition_profiles_id_seq; Type: SEQUENCE; Schema: nutrition; Owner: postgres
--

CREATE SEQUENCE nutrition.user_nutrition_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE nutrition.user_nutrition_profiles_id_seq OWNER TO postgres;

--
-- Name: user_nutrition_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: nutrition; Owner: postgres
--

ALTER SEQUENCE nutrition.user_nutrition_profiles_id_seq OWNED BY nutrition.user_nutrition_profiles.id;


--
-- Name: ejercicios id; Type: DEFAULT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.ejercicios ALTER COLUMN id SET DEFAULT nextval('gym.ejercicios_id_seq'::regclass);


--
-- Name: fitbit_auth_temp id; Type: DEFAULT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_auth_temp ALTER COLUMN id SET DEFAULT nextval('gym.fitbit_auth_temp_id_seq'::regclass);


--
-- Name: fitbit_tokens id; Type: DEFAULT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_tokens ALTER COLUMN id SET DEFAULT nextval('gym.fitbit_tokens_id_seq'::regclass);


--
-- Name: rutinas id; Type: DEFAULT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.rutinas ALTER COLUMN id SET DEFAULT nextval('gym.rutinas_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.users ALTER COLUMN id SET DEFAULT nextval('gym.users_id_seq'::regclass);


--
-- Name: daily_tracking id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.daily_tracking ALTER COLUMN id SET DEFAULT nextval('nutrition.daily_tracking_id_seq'::regclass);


--
-- Name: ingredients id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.ingredients ALTER COLUMN id SET DEFAULT nextval('nutrition.ingredients_id_seq'::regclass);


--
-- Name: meal_ingredients id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_ingredients ALTER COLUMN id SET DEFAULT nextval('nutrition.meal_ingredients_id_seq'::regclass);


--
-- Name: meal_plan_items id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plan_items ALTER COLUMN id SET DEFAULT nextval('nutrition.meal_plan_items_id_seq'::regclass);


--
-- Name: meal_plans id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plans ALTER COLUMN id SET DEFAULT nextval('nutrition.meal_plans_id_seq'::regclass);


--
-- Name: meals id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meals ALTER COLUMN id SET DEFAULT nextval('nutrition.meals_id_seq'::regclass);


--
-- Name: user_nutrition_profiles id; Type: DEFAULT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.user_nutrition_profiles ALTER COLUMN id SET DEFAULT nextval('nutrition.user_nutrition_profiles_id_seq'::regclass);


--
-- Name: ejercicios ejercicios_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.ejercicios
    ADD CONSTRAINT ejercicios_pkey PRIMARY KEY (id);


--
-- Name: fitbit_auth_temp fitbit_auth_temp_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_auth_temp
    ADD CONSTRAINT fitbit_auth_temp_pkey PRIMARY KEY (id);


--
-- Name: fitbit_auth_temp fitbit_auth_temp_user_id_client_id_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_auth_temp
    ADD CONSTRAINT fitbit_auth_temp_user_id_client_id_key UNIQUE (user_id, client_id);


--
-- Name: fitbit_tokens fitbit_tokens_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_tokens
    ADD CONSTRAINT fitbit_tokens_pkey PRIMARY KEY (id);


--
-- Name: fitbit_tokens fitbit_tokens_user_id_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_tokens
    ADD CONSTRAINT fitbit_tokens_user_id_key UNIQUE (user_id);


--
-- Name: fitbit_tokens fitbit_tokens_user_uuid_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_tokens
    ADD CONSTRAINT fitbit_tokens_user_uuid_key UNIQUE (user_uuid);


--
-- Name: link_codes link_codes_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.link_codes
    ADD CONSTRAINT link_codes_pkey PRIMARY KEY (code);


--
-- Name: rutinas rutinas_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.rutinas
    ADD CONSTRAINT rutinas_pkey PRIMARY KEY (id);


--
-- Name: rutinas rutinas_user_id_dia_semana_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.rutinas
    ADD CONSTRAINT rutinas_user_id_dia_semana_key UNIQUE (user_id, dia_semana);


--
-- Name: rutinas rutinas_user_uuid_dia_semana_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.rutinas
    ADD CONSTRAINT rutinas_user_uuid_dia_semana_key UNIQUE (user_uuid, dia_semana);


--
-- Name: users users_google_id_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.users
    ADD CONSTRAINT users_google_id_key UNIQUE (google_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_id_key; Type: CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.users
    ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);


--
-- Name: daily_tracking daily_tracking_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.daily_tracking
    ADD CONSTRAINT daily_tracking_pkey PRIMARY KEY (id);


--
-- Name: daily_tracking daily_tracking_user_id_tracking_date_key; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.daily_tracking
    ADD CONSTRAINT daily_tracking_user_id_tracking_date_key UNIQUE (user_id, tracking_date);


--
-- Name: ingredients ingredients_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.ingredients
    ADD CONSTRAINT ingredients_pkey PRIMARY KEY (id);


--
-- Name: meal_ingredients meal_ingredients_meal_id_ingredient_id_key; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_ingredients
    ADD CONSTRAINT meal_ingredients_meal_id_ingredient_id_key UNIQUE (meal_id, ingredient_id);


--
-- Name: meal_ingredients meal_ingredients_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_ingredients
    ADD CONSTRAINT meal_ingredients_pkey PRIMARY KEY (id);


--
-- Name: meal_plan_items meal_plan_items_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plan_items
    ADD CONSTRAINT meal_plan_items_pkey PRIMARY KEY (id);


--
-- Name: meal_plans meal_plans_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plans
    ADD CONSTRAINT meal_plans_pkey PRIMARY KEY (id);


--
-- Name: meals meals_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meals
    ADD CONSTRAINT meals_pkey PRIMARY KEY (id);


--
-- Name: user_nutrition_profiles user_nutrition_profiles_pkey; Type: CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.user_nutrition_profiles
    ADD CONSTRAINT user_nutrition_profiles_pkey PRIMARY KEY (id);


--
-- Name: idx_fitbit_user_id; Type: INDEX; Schema: gym; Owner: postgres
--

CREATE INDEX idx_fitbit_user_id ON gym.fitbit_tokens USING btree (user_id);


--
-- Name: idx_users_google_id; Type: INDEX; Schema: gym; Owner: postgres
--

CREATE INDEX idx_users_google_id ON gym.users USING btree (google_id);


--
-- Name: idx_users_telegram_id; Type: INDEX; Schema: gym; Owner: postgres
--

CREATE INDEX idx_users_telegram_id ON gym.users USING btree (telegram_id);


--
-- Name: idx_daily_tracking_date; Type: INDEX; Schema: nutrition; Owner: postgres
--

CREATE INDEX idx_daily_tracking_date ON nutrition.daily_tracking USING btree (tracking_date DESC);


--
-- Name: idx_daily_tracking_user_date; Type: INDEX; Schema: nutrition; Owner: postgres
--

CREATE INDEX idx_daily_tracking_user_date ON nutrition.daily_tracking USING btree (user_id, tracking_date);


--
-- Name: idx_meal_plan_items_meal_plan_id; Type: INDEX; Schema: nutrition; Owner: postgres
--

CREATE INDEX idx_meal_plan_items_meal_plan_id ON nutrition.meal_plan_items USING btree (meal_plan_id);


--
-- Name: idx_meal_plans_user_id; Type: INDEX; Schema: nutrition; Owner: postgres
--

CREATE INDEX idx_meal_plans_user_id ON nutrition.meal_plans USING btree (user_id);


--
-- Name: ejercicios ejercicios_user_uuid_fkey; Type: FK CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.ejercicios
    ADD CONSTRAINT ejercicios_user_uuid_fkey FOREIGN KEY (user_uuid) REFERENCES gym.users(id);


--
-- Name: fitbit_tokens fitbit_tokens_user_uuid_fkey; Type: FK CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.fitbit_tokens
    ADD CONSTRAINT fitbit_tokens_user_uuid_fkey FOREIGN KEY (user_uuid) REFERENCES gym.users(id);


--
-- Name: link_codes link_codes_user_id_fkey; Type: FK CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.link_codes
    ADD CONSTRAINT link_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES gym.users(id);


--
-- Name: rutinas rutinas_user_uuid_fkey; Type: FK CONSTRAINT; Schema: gym; Owner: postgres
--

ALTER TABLE ONLY gym.rutinas
    ADD CONSTRAINT rutinas_user_uuid_fkey FOREIGN KEY (user_uuid) REFERENCES gym.users(id);


--
-- Name: meal_ingredients meal_ingredients_ingredient_id_fkey; Type: FK CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_ingredients
    ADD CONSTRAINT meal_ingredients_ingredient_id_fkey FOREIGN KEY (ingredient_id) REFERENCES nutrition.ingredients(id) ON DELETE CASCADE;


--
-- Name: meal_ingredients meal_ingredients_meal_id_fkey; Type: FK CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_ingredients
    ADD CONSTRAINT meal_ingredients_meal_id_fkey FOREIGN KEY (meal_id) REFERENCES nutrition.meals(id) ON DELETE CASCADE;


--
-- Name: meal_plan_items meal_plan_items_meal_id_fkey; Type: FK CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plan_items
    ADD CONSTRAINT meal_plan_items_meal_id_fkey FOREIGN KEY (meal_id) REFERENCES nutrition.meals(id);


--
-- Name: meal_plan_items meal_plan_items_meal_plan_id_fkey; Type: FK CONSTRAINT; Schema: nutrition; Owner: postgres
--

ALTER TABLE ONLY nutrition.meal_plan_items
    ADD CONSTRAINT meal_plan_items_meal_plan_id_fkey FOREIGN KEY (meal_plan_id) REFERENCES nutrition.meal_plans(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

