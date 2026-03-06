from background.modules.postgres import *

class ReuseDataDao():
    """
    indeed bellow for clean old db
    - db function remove_old_trading_reuse_data
    - db trigger trading_reuse_data_trigger
    
    """
    
    def __init__(self):
        self.postgres = Postgres()
    
    def read_reusable_data(self, key):

        query = f"""
        SELECT
            seq,
            key,
            value,
            reg_dt,
            use_dt
        FROM
            reusable_data
        WHERE
            key = '{key}'
        ORDER BY
            seq DESC;
        """
        return self.postgres.read_one(query).get("value")
    
    def upsert_reusable_data(self, key, value):
        
        reuse_prev = self.read_reusable_data(key)
        if not reuse_prev:
            self.insert_reusable_data(key, value)
        
        else:
            self.update_reusable_data(key)
    
    def insert_reusable_data(self, key, value):
        
        query = f"""
        INSERT INTO reusable_data
        (key, value, reg_dt, use_dt)
        VALUES('{key}', '{value}', now(), now());
        """
        return self.postgres.execute_query_with_commit(query) 
        
    def update_reusable_data(self, key):
        
        query = f"""
        UPDATE reusable_data SET
        use_dt = now()
        WHERE key = '{key}'
        """
        return self.postgres.execute_query_with_commit(query) 
    
reuse_data_dao = ReuseDataDao()
