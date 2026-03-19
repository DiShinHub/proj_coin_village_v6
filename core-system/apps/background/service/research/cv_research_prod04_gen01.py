from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import os
import datetime

class CvResearchProd03Gen01(ServiceHandler):
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
    
    def main(self):

        try:
            for ticker in self.tickers:
                
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.hot_time()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def hot_time(self, interval="minute5", days=90, count=200):
        """
        시간대별 거래량 / 임밸런스 분석
        """

        try:
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

            volume_by_weekday = df.groupby("weekday")["volume"].mean()
            imbalance_by_weekday = df.groupby("weekday")["volume_imbalance"].mean()

            # 4. HOT TIME 추출
            top_volume_hours = volume_by_hour.sort_values(ascending=False).head(5).index.tolist()

            # 방향성
            best_long_hours = imbalance_by_hour.sort_values(ascending=False).head(3).index.tolist()
            best_short_hours = imbalance_by_hour.sort_values(ascending=True).head(3).index.tolist()

            # 5. 점수화 (선택)
            norm_volume = (volume_by_hour - volume_by_hour.min()) / (volume_by_hour.max() - volume_by_hour.min() + 1e-9)
            norm_imbalance = imbalance_by_hour / (abs(imbalance_by_hour).max() + 1e-9)

            hot_score = (norm_volume * 0.7 + abs(norm_imbalance) * 0.3)

            # 6. 결과 JSON
            result_json = {
                "volume_by_hour": volume_by_hour.to_dict(),
                "imbalance_by_hour": imbalance_by_hour.to_dict(),
                "volume_by_weekday": volume_by_weekday.to_dict(),
                "imbalance_by_weekday": imbalance_by_weekday.to_dict(),
                "top_volume_hours": top_volume_hours,
                "best_long_hours": best_long_hours,
                "best_short_hours": best_short_hours,
                "hot_score_by_hour": hot_score.to_dict()
            }

            # 7. DB 저장
            params = {}
            params["runnable_service_seq"] = self.seq
            params["type"] = "upbit-hot-time"
            params["exchange"] = "upbit"
            params["ticker"] = self.ticker
            params["tags"] = ["upbit", "hot_time", "volume"]
            params["result_markerable"] = float(max(hot_score)) if len(hot_score) > 0 else 0
            params["result_json"] = result_json
            params["result_txt"] = ""
            params["reg_member_seq"] = 0
            params["mod_member_seq"] = 0

            self.research_result_dao.insert_with_limit(params, 10000)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")