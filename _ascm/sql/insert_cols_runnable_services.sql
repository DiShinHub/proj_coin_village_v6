DELETE FROM runnable_services;

INSERT INTO public.runnable_services (seq, execution_path, execution_class, execution_method, service_options, product_name, product_desc, reg_dt, reg_member_seq, mod_dt, mod_member_seq, activate_yn, delete_yn) VALUES
(1, 'background.service.test.cv_test', 'CvTest', 'run', '{}', '', '', now(), 0, now(), 0, 'Y'::character varying, 'Y'::character varying)
(2, 'background.service.system.cv_redis_cleaner_gen01', 'CvRedisCleanerGen01', 'run', '{}', '', '', now(), 0, now(), 0, 'Y'::character varying, 'Y'::character varying)

;
