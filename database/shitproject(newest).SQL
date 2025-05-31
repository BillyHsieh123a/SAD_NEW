-- 建立序列
CREATE SEQUENCE IF NOT EXISTS clothes_id_seq;
CREATE SEQUENCE IF NOT EXISTS tryon_id_seq;
CREATE SEQUENCE IF NOT EXISTS user_id_seq;

-- Table: public.users

-- DROP TABLE IF EXISTS public.users;

CREATE TABLE IF NOT EXISTS public.users
(
    user_id bigint NOT NULL DEFAULT nextval('user_id_seq'::regclass),
    password character varying(20) COLLATE pg_catalog."default" NOT NULL,
    name character varying(40) COLLATE pg_catalog."default",
    CONSTRAINT user_pkey PRIMARY KEY (user_id)
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.users
    OWNER to postgres;


-- Table: public.Clothes

-- DROP TABLE IF EXISTS public."Clothes";

CREATE TABLE IF NOT EXISTS public."Clothes"
(
    user_id bigint NOT NULL,
    clothes_id bigint NOT NULL DEFAULT nextval('clothes_id_seq'::regclass),
    type character varying COLLATE pg_catalog."default" NOT NULL,
    filepath character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Clothes_pkey" PRIMARY KEY (user_id, clothes_id),
    CONSTRAINT unique_clothes UNIQUE (clothes_id),
    CONSTRAINT fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH FULL
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT "Clothes_type_check" CHECK (type::text = ANY (ARRAY['Tops'::character varying, 'Bottoms'::character varying]::text[]))
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public."Clothes"
    OWNER to postgres;


-- Table: public.TryonResults

-- DROP TABLE IF EXISTS public."TryonResults";

CREATE TABLE IF NOT EXISTS public."TryonResults"
(
    user_id bigint NOT NULL,
    try_on_id bigint NOT NULL DEFAULT nextval('tryon_id_seq'::regclass),
    top_id bigint,
    bottom_id bigint,
    comments character varying COLLATE pg_catalog."default",
    filepath character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT pk_tryon PRIMARY KEY (try_on_id),
    CONSTRAINT fk_bottoms FOREIGN KEY (bottom_id)
        REFERENCES public."Clothes" (clothes_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_tops FOREIGN KEY (top_id)
        REFERENCES public."Clothes" (clothes_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public."TryonResults"
    OWNER to postgres;


-- Index: fki_fk_bottoms

-- DROP INDEX IF EXISTS public.fki_fk_bottoms;

CREATE INDEX IF NOT EXISTS fki_fk_bottoms
    ON public."TryonResults" USING btree
    (bottom_id ASC NULLS LAST)
    TABLESPACE pg_default;

-- Index: fki_fk_tops

-- DROP INDEX IF EXISTS public.fki_fk_tops;

CREATE INDEX IF NOT EXISTS fki_fk_tops
    ON public."TryonResults" USING btree
    (top_id ASC NULLS LAST)
    TABLESPACE pg_default;


-- Table: public.user_photo

-- DROP TABLE IF EXISTS public.user_photo;

CREATE TABLE IF NOT EXISTS public.user_photo
(
    user_id bigint NOT NULL,
    filepath character varying COLLATE pg_catalog."default" NOT NULL,
    photo_id bigint NOT NULL,
    CONSTRAINT user_photo_pkey PRIMARY KEY (user_id, photo_id)
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_photo
    OWNER to postgres;
