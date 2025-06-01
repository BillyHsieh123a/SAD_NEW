--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

-- Started on 2025-06-01 00:30:50

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 4826 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- TOC entry 847 (class 1247 OID 25242)
-- Name: cloth_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.cloth_type AS ENUM (
    'upper',
    'lower',
    'full_set'
);


ALTER TYPE public.cloth_type OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 25307)
-- Name: Clothes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Clothes" (
    user_id bigint NOT NULL,
    clothes_id bigint NOT NULL,
    type character varying NOT NULL,
    filepath character varying NOT NULL,
    CONSTRAINT "Clothes_type_check" CHECK (((type)::text = ANY ((ARRAY['top'::character varying, 'bottom'::character varying])::text[])))
);


ALTER TABLE public."Clothes" OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 25385)
-- Name: TryonResults; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."TryonResults" (
    user_id bigint NOT NULL,
    try_on_id bigint NOT NULL,
    top_id bigint,
    bottom_id bigint,
    comments character varying,
    filepath character varying NOT NULL
);


ALTER TABLE public."TryonResults" OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 25410)
-- Name: clothes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.clothes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clothes_id_seq OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 25091)
-- Name: order_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.order_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_id_seq OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 25411)
-- Name: photo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.photo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.photo_id_seq OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 25118)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    password character varying(20) NOT NULL,
    name character varying(40)
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 25121)
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO postgres;

--
-- TOC entry 4828 (class 0 OID 0)
-- Dependencies: 217
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_id_seq OWNED BY public.users.user_id;


--
-- TOC entry 218 (class 1259 OID 25300)
-- Name: user_photo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_photo (
    user_id bigint NOT NULL,
    filepath character varying NOT NULL,
    photo_id bigint NOT NULL
);


ALTER TABLE public.user_photo OWNER TO postgres;

--
-- TOC entry 4652 (class 2604 OID 25232)
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- TOC entry 4817 (class 0 OID 25307)
-- Dependencies: 219
-- Data for Name: Clothes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."Clothes" (user_id, clothes_id, type, filepath) FROM stdin;
\.


--
-- TOC entry 4818 (class 0 OID 25385)
-- Dependencies: 220
-- Data for Name: TryonResults; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."TryonResults" (user_id, try_on_id, top_id, bottom_id, comments, filepath) FROM stdin;
\.


--
-- TOC entry 4816 (class 0 OID 25300)
-- Dependencies: 218
-- Data for Name: user_photo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_photo (user_id, filepath, photo_id) FROM stdin;
\.


--
-- TOC entry 4814 (class 0 OID 25118)
-- Dependencies: 216
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, password, name) FROM stdin;
0	default	\N
2	dami	\N
1	billy	billy@gmail.com
19	12340987	liu.shiquan@ntusa.ntu.edu.tw
20	12340987	liu.shiquan@ntusa.ntu.edu.tw
21	11111111	b11705059@ntu.edu.tw
22	22222222	ryan1302tw@gmail.com
23	33333333	b11705059@g.ntu.edu.tw
\.


--
-- TOC entry 4829 (class 0 OID 0)
-- Dependencies: 221
-- Name: clothes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clothes_id_seq', 1, false);


--
-- TOC entry 4830 (class 0 OID 0)
-- Dependencies: 215
-- Name: order_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.order_id_seq', 13, true);


--
-- TOC entry 4831 (class 0 OID 0)
-- Dependencies: 222
-- Name: photo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.photo_id_seq', 1, false);


--
-- TOC entry 4832 (class 0 OID 0)
-- Dependencies: 217
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 23, true);


--
-- TOC entry 4659 (class 2606 OID 25314)
-- Name: Clothes pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clothes"
    ADD CONSTRAINT pk PRIMARY KEY (user_id, clothes_id);


--
-- TOC entry 4665 (class 2606 OID 25391)
-- Name: TryonResults pk_tryon; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."TryonResults"
    ADD CONSTRAINT pk_tryon PRIMARY KEY (try_on_id);


--
-- TOC entry 4661 (class 2606 OID 25367)
-- Name: Clothes unique_clothes; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clothes"
    ADD CONSTRAINT unique_clothes UNIQUE (clothes_id);


--
-- TOC entry 4657 (class 2606 OID 25306)
-- Name: user_photo user_photo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_photo
    ADD CONSTRAINT user_photo_pkey PRIMARY KEY (user_id, photo_id);


--
-- TOC entry 4655 (class 2606 OID 25151)
-- Name: users user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4662 (class 1259 OID 25412)
-- Name: fki_fk_bottoms; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_fk_bottoms ON public."TryonResults" USING btree (bottom_id);


--
-- TOC entry 4663 (class 1259 OID 25413)
-- Name: fki_fk_tops; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_fk_tops ON public."TryonResults" USING btree (top_id);


--
-- TOC entry 4666 (class 2606 OID 25315)
-- Name: Clothes fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Clothes"
    ADD CONSTRAINT fk FOREIGN KEY (user_id) REFERENCES public.users(user_id) MATCH FULL;


--
-- TOC entry 4667 (class 2606 OID 25402)
-- Name: TryonResults fk_bottoms; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."TryonResults"
    ADD CONSTRAINT fk_bottoms FOREIGN KEY (bottom_id) REFERENCES public."Clothes"(clothes_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4668 (class 2606 OID 25397)
-- Name: TryonResults fk_tops; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."TryonResults"
    ADD CONSTRAINT fk_tops FOREIGN KEY (top_id) REFERENCES public."Clothes"(clothes_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4669 (class 2606 OID 25392)
-- Name: TryonResults fk_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."TryonResults"
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4827 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


-- Completed on 2025-06-01 00:30:50

--
-- PostgreSQL database dump complete
--

