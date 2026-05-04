from background.middlewares.service_handler import ServiceHandler

from background.modules.log import Log
from background.modules.redis import Redis
from background.modules.exchange_upbit import ExChangeUpbit

from background.constance.upbit_constance import UpbitConst

import os
import time
import json

class CvRedisCleanerGen01(ServiceHandler):
    """
    Service Code : CvRedisCleaner
    Generation : 01 
    
    Desc : 
    - 레디스 플러시
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
        self.target_term = self.service_options["target_term"]
        self.interval_ = self.service_options["interval"]

    def main(self):

        try:
            self.upbit.set_ticker(self.ticker)
            df = self.upbit.set_ohlcvs(interval="minute1", count=200, days=90, from_=self.target_term["from"], to_=self.target_term["to"])
            self.replay_df_to_queue(df)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    """
    biz
    """
    def replay_df_to_queue(self, df, speed=1.0):
        
        for _, row in df.iterrows():
            
            ts = int(row["datetime"].timestamp() * 1000)
            
            event = {
                "code": self.ticker,
                "trade_price": row["close"],
                "timestamp": ts
            }
            key = f"{UpbitConst.ORDERBOOK_QUEUE_KEY}_{self.ticker}_{ts}"
            self.push_to_queue(key, json.dumps(event))
            time.sleep(speed)
        
    def push_to_queue(self, key, message):

        self.redis.set_data(
            key=key,
            val=message, 
            expire=self.service_options.get("ttl_orderbook")
        )