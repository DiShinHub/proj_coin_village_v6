-- public.runnable_services 
DROP TABLE IF EXISTS public.runnable_services;
CREATE TABLE public.runnable_services (
    seq SERIAL PRIMARY KEY,
    execution_path varchar(255) NOT NULL,
    execution_class varchar(255) NOT NULL,
    execution_method varchar(255) NOT NULL,
    service_options jsonb
    product_name varchar(100) NOT NULL,
    product_desc varchar(255),
    reg_dt timestamp with time zone,
    reg_member_seq integer NOT NULL,
    mod_dt timestamp with time zone,
    mod_member_seq integer NOT NULL,
    activate_yn varchar(1) NOT NULL DEFAULT 'Y'::character varying,
    delete_yn varchar(1) NOT NULL DEFAULT 'Y'::character varying,
);
CREATE INDEX ix_runnable_services_execution_method ON public.runnable_services (execution_method);