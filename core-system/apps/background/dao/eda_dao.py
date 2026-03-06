from background.modules.postgres import *

class EdaDao():
    
    def __init__(self):
        self.postgres = Postgres()

    def insert_eda_images(self, params):

        # base query
        query = f"""
            INSERT INTO public.eda_images
            (seq, exchange, ticker, minio_path, description, reg_dt, mod_dt)
            VALUES(nextval('eda_images_seq_seq'::regclass), 
            '{params['exchange']}', 
            '{params['ticker']}', 
            '{params['minio_path']}', 
            '{params['description']}', 
            now(), 
            now());
        """
        
        # execute
        res = self.postgres.execute_query_with_commit(query)
        return res

    def get_eda_image_by_minio_path(self, minio_path=None):

        query = f"""
            select
                seq,
                exchange,
                ticker,
                minio_path,
                description
            from
                eda_images
            WHERE 1=1
                
        """
        if minio_path:
            query += f""" AND minio_path = '{minio_path}'"""

        return self.postgres.read_one(query) 

    def update_eda_images(self, params, seq):

        # base query
        query = f"""
            UPDATE eda_images SET
        """
        
        # set query
        set_cluase = ""
        for key, val in params.items():
            set_cluase = f""" {key} = '{val}',"""
        if not set_cluase:
            raise Exception("no params found")
        
        set_cluase = set_cluase[:-1]
        
        # where query
        where_cluase = f" WHERE seq = {seq}"
        
        # bind
        query += set_cluase
        query += where_cluase
        
        # execute
        res = self.postgres.execute_query_with_commit(query)
        return res
    
    def upsert_eda_images(self, params):

        eda_images = self.get_eda_image_by_minio_path(params["minio_path"])
        if len(eda_images) > 0:
            self.update_eda_images(params, eda_images["seq"])

        else:
            self.insert_eda_images(params)