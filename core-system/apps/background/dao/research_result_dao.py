from background.modules.postgres import *
import json

class ResearchResultDao:

    def __init__(self):
        self.postgres = Postgres()

    def insert(self, params):

        tags = "NULL"
        if params.get("tags"):
            tags = "ARRAY[" + ",".join([f"'{t}'" for t in params["tags"]]) + "]"

        result_json = "NULL"
        if params.get("result_json"):
            result_json = f"""'{json.dumps(params["result_json"])}'::jsonb"""

        reg_dt = 'now()'
        if params.get("reg_dt"):
            reg_dt = f"{params.get('reg_dt')}"

        mod_dt = 'now()'
        if params.get("mod_dt"):
            mod_dt = f"{params.get('mod_dt')}"

        query = f"""
        INSERT INTO research_result
        (
            runnable_service_seq,
            type,
            exchange,
            ticker,
            tags,
            result_markerable,
            result_json,
            result_txt,
            reg_dt,
            reg_member_seq,
            mod_dt,
            mod_member_seq
        )
        VALUES
        (
            {params.get("runnable_service_seq", "NULL")},
            '{params.get("type")}',
            '{params.get("exchange")}',
            '{params.get("ticker")}',
            {tags},
            '{params.get("result_markerable")}',
            {result_json},
            '{params.get("result_txt")}',
            '{reg_dt}',
            {params.get("reg_member_seq")},
            '{mod_dt}',
            {params.get("mod_member_seq")}
        )
        """
        return self.postgres.execute_query_with_commit(query)
    
    def get(self, runnable_service_seq=None, type=None, exchange=None, ticker=None):

        query = """
            SELECT
                seq,
                runnable_service_seq,
                type,
                exchange,
                ticker,
                tags,
                result_markerable,
                result_json,
                result_txt,
                reg_dt
            FROM research_result
            WHERE 1=1
        """
        if runnable_service_seq:
            query += f" AND runnable_service_seq = {runnable_service_seq}"

        if exchange:
            query += f" AND exchange = '{exchange}'"

        if type:
            query += f" AND type = '{type}'"

        if ticker:
            query += f" AND ticker = '{ticker}'"

        return self.postgres.read_one(query) 
    
    def gets(self, 
            page_no: int = 1,
            row_count: int = 10,
            runnable_service_seq=None, 
            type=None, 
            exchange=None, 
            ticker=None,
        ):
        
        query = """
            SELECT
                seq,
                runnable_service_seq,
                type,
                exchange,
                ticker,
                tags,
                result_markerable,
                result_json,
                result_txt,
                reg_dt
            FROM research_result
            WHERE 1=1
        """
        if runnable_service_seq:
            query += f" AND runnable_service_seq = {runnable_service_seq}"

        if exchange:
            query += f" AND exchange = '{exchange}'"

        if type:
            query += f" AND type = '{type}'"

        if ticker:
            query += f" AND ticker = '{ticker}'"
        
        query += f" ORDER BY seq DESC"
        query += f""" LIMIT {row_count} OFFSET {(page_no - 1) * row_count} """ 
        
        return self.postgres.read_all(query) 
    
    def update(self, seq, params):

        set_clause = ""
        for key, val in params.items():

            if key == "tags":
                val = "ARRAY[" + ",".join([f"'{t}'" for t in val]) + "]"

            elif key == "result_json":
                val = f"""'{json.dumps(val)}'::jsonb"""

            else:
                val = f"'{val}'"

            set_clause += f"{key} = {val},"

        if not set_clause:
            raise Exception("no params")

        set_clause = set_clause[:-1]

        query = f"""
            UPDATE research_result
            SET
                {set_clause},
                mod_dt = now()
            WHERE seq = {seq}
        """
        return self.postgres.execute_query_with_commit(query)
    
    def upsert(self, params):

        res = self.get(
            runnable_service_seq=params.get("runnable_service_seq"),
            exchange=params.get("exchange"),
            ticker=params.get("ticker"),
        )
        if res:
            self.update(res["seq"], params)

        else:
            self.insert(params)
    
    def insert_with_limit(self, params, limit=1000):

        self.insert(params)

        query = f"""
            WITH old_rows AS (
                SELECT seq
                FROM research_result
                WHERE runnable_service_seq = {params.get("runnable_service_seq")}
                AND exchange = '{params.get("exchange")}'
                AND ticker = '{params.get("ticker")}'
                ORDER BY seq DESC
                OFFSET {limit}
            )
            DELETE FROM research_result
            WHERE seq IN (SELECT seq FROM old_rows);
        """

        return self.postgres.execute_query_with_commit(query)