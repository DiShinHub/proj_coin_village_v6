from background.middlewares.service_handler import ServiceHandler

from background.modules.log import Log
from background.modules.redis import Redis
from background.modules.exchange_upbit import ExChangeUpbit

from background.constance.upbit_constance import UpbitConst

import pandas as pd
import os
import time
import json

class CvRequestGeneratorGen01(ServiceHandler):
    """
    Service Code : CvRequestGenerator
    Generation : 01 
    
    Desc : 
    - 
    """

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        super().__init__(seq, interval_options, schedule_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = Redis()
        self.upbit = ExChangeUpbit()

        self.ticker = self.service_options["ticker"]
        self.term_from = self.service_options["term_from"]

        self.term_to = self.service_options["term_to"]
        self.interval_ = self.service_options["interval"]

    def main(self):

        try:
            self.upbit.set_ticker(self.ticker)
            df = self.upbit.set_ohlcvs(interval=self.interval_, count=200, days=90, from_=self.term_from, to_=self.term_to)

            self.replay_df_to_queue(df, 0.5)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    """
    biz
    """
    def replay_df_to_queue(self, df, speed=1.0):
        
        for _, row in df.iterrows():
            dt = row["datetime"]
            dt = dt.tz_localize("Asia/Seoul")
            ts = int(dt.timestamp())*1000

            event = {
                "code": self.ticker,
                "trade_price": row["close"],
                "timestamp": ts,
                "order_book_date": str(row["datetime"])
            }
            key = f"{UpbitConst.ORDERBOOK_QUEUE_KEY}_{self.ticker}_{ts}"
            self.push_to_queue(key, json.dumps(event))
            time.sleep(speed)
        
    def push_to_queue(self, key, message):

        self.redis.set_data(
            key=key,
            val=message, 
            expire=60
        )