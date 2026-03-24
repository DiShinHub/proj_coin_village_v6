from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import os
import datetime

class CvResearchProd04Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd04Gen01
    Generation : 01 
    
    Desc : 
    - 핫 독
    """
    pref_slack_msg_box = ""

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        ServiceHandler.__init__(self, schedule_options=schedule_options, interval_options=interval_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = redis_single
        self.upbit = ExChangeUpbit()

        self.research_result_dao = ResearchResultDao()

        self.tickers = self.service_options.get("tickers")
        self.ticker = None
        
        self.target_days_list = [
            31,
            62,
            93,
            # 186
        ]
    
    def main(self):

        try:
            for ticker in self.tickers:
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.upbit.set_ticker(self.ticker)
                self.decide_hot_cold_time()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def decide_hot_cold_time(self, interval="minute5", anchor_days="62"):
        
        try:
            count=200
            hot_cold_total = {}
            for days in self.target_days_list:
                
                # 1. 데이터 수집
                to_ = datetime.datetime.now()
                from_ = to_ - datetime.timedelta(days=days)
    
                self.upbit.set_ohlcvs(
                    interval=interval, 
                    days=days, 
                    count=count, 
                    from_=from_, 
                    to_=to_
                )
    
                df = self.upbit.set_volume_imbalance()
                df = self.upbit.set_hour()
                df = self.upbit.set_weekday()
    
                if df is None or len(df) == 0:
                    return
    
                # 2. 기본 컬럼 체크
                required_cols = ["volume", "volume_imbalance", "hour", "weekday"]
    
                for col in required_cols:
                    if col not in df.columns:
                        self.log.info(f"[{self.ticker}] missing column: {col}")
                        return
    
                # 3. 시간대별 집계
                volume_by_hour = df.groupby("hour")["volume"].mean()
                imbalance_by_hour = df.groupby("hour")["volume_imbalance"].mean()
    
                # volume_by_weekday = df.groupby("weekday")["volume"].mean()
                # imbalance_by_weekday = df.groupby("weekday")["volume_imbalance"].mean()
    
                # 4. HOT TIME 추출
                top_volume_hours = volume_by_hour.sort_values(ascending=False).head(5).index.tolist()
                bot_volume_hours = volume_by_hour.sort_values(ascending=True).head(5).index.tolist()
    
                # 방향성
                best_long_hours = imbalance_by_hour.sort_values(ascending=False).head(5).index.tolist()
                best_short_hours = imbalance_by_hour.sort_values(ascending=True).head(5).index.tolist()

                hot_cold_total[str(days)] = {
                    "top_volume_hours" : top_volume_hours,
                    "bot_volume_hours" : bot_volume_hours,
                    "best_long_hours" : best_long_hours,
                    "best_short_hours" : best_short_hours,
                    
                }
        
            result_json = hot_cold_total
            result_markerable = str(hot_cold_total[anchor_days]["best_long_hours"])

            params = {}
            params["runnable_service_seq"] = self.seq
            params["type"] = "upbit-hot/cold-time"
            params["exchange"] = "upbit"
            params["ticker"] = self.ticker
            params["tags"] = ["upbit", "hot/cold-time"]
            params["result_markerable"] = result_markerable
            params["result_json"] = result_json
            params["result_txt"] = ""
            params["reg_member_seq"] = 0
            params["mod_member_seq"] = 0

            self.research_result_dao.insert_with_limit(params, 10000)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")