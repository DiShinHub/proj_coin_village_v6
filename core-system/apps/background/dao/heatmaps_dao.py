from background.modules.postgres import *

class HeatmapsDao():
    
    def __init__(self):
        self.postgres = Postgres()

    def insert_heatmaps_volume_time_week(self, params):

        # base query
        query = f"""
            INSERT INTO public.eda_images
            (seq, exchange, ticker, minio_path, description, reg_dt, mod_dt)
            VALUES(nextval('eda_images_seq_seq'::regclass), 
            '{params['ticker']}', 
            '{params['term']}', 
            '{params['minio_path']}', 
            now(), 
            now());
        """
        
        # execute
        res = self.postgres.execute_query_with_commit(query)
        return res

    def get_heatmaps_volume_time_week(self, ticker=None, term=None):

        query = f"""
            select
                seq,
                ticker,
                term,
                minio_path
            from
                heatmaps_volume_time_week
            WHERE 1=1
                
        """
        if ticker:
            query += f""" AND ticker = '{ticker}'"""
        if term:
            query += f""" AND term = '{term}'"""

        return self.postgres.read_one(query) 

    def update_heatmaps_volume_time_week(self, params, seq):

        # base query
        query = f"""
            UPDATE heatmaps_volume_time_week SET
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
    
    def upsert_heatmaps_volume_time_week(self, params):

        heatmaps_volume_time_week = self.get_heatmaps_volume_time_week(params["ticker"], params["term"])
        if len(heatmaps_volume_time_week) > 0:
            self.update_heatmaps_volume_time_week(params, heatmaps_volume_time_week["seq"])

        else:
            self.insert_heatmaps_volume_time_week(params)