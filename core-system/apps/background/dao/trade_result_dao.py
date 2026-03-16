from background.modules.postgres import *
import json

class TradeResultDao:

    def __init__(self):
        self.postgres = Postgres()

    def insert(self, params):

        query = f"""
            INSERT INTO trade_result
            (
                exchange,
                ticker,
                uuid,
                ord_side,
                ord_type,
                price,
                reserved_fee,
                remaining_fee,
                paid_fee,
                state,
                locked,
                executed_volume,
                runnable_service_seq,
                reg_dt,
                mod_dt
            )
            VALUES
            (
                '{params.get("exchange")}',
                '{params.get("ticker")}',
                '{params.get("uuid")}',
                '{params.get("ord_side")}',
                '{params.get("ord_type")}',
                '{params.get("price")}',
                '{params.get("reserved_fee")}',
                '{params.get("remaining_fee")}',
                '{params.get("paid_fee")}',
                '{params.get("state")}',
                '{params.get("locked")}',
                '{params.get("executed_volume")}',
                {params.get("runnable_service_seq")},
                now(),
                now()
            )
        """
        return self.postgres.execute_query_with_commit(query)

    def get(self, uuid=None, exchange=None, ticker=None):

        query = """
        SELECT
            seq,
            exchange,
            ticker,
            uuid,
            ord_side,
            ord_type,
            price,
            reserved_fee,
            remaining_fee,
            paid_fee,
            state,
            locked,
            executed_volume,
            runnable_service_seq,
            reg_dt
        FROM trade_result
        WHERE 1=1
        """
        if uuid:
            query += f" AND uuid = '{uuid}'"

        if exchange:
            query += f" AND exchange = '{exchange}'"

        if ticker:
            query += f" AND ticker = '{ticker}'"

        return self.postgres.read_one(query)
