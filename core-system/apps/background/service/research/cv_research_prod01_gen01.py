from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import pandas as pd
import os
import datetime

class CvResearchProd01Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd01Gen01
    Generation : 01 
    
    Desc : 
    - 도날드 덕 
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
        self.k_dict = {
            "minute1" : 1.4, 
            "minute3" : 1.4, 
            "minute5" : 1.4,
            "minute10" : 1.4, 
            "minute15" : 1.4, 
            "minute30" : 1.4,
            "minute60" : 1.4, 
        }
    
    def main(self):

        try:
            for ticker in self.tickers:
                
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.decide_regime()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
            
    def decide_regime(self, anchor_days="62", anchor_interval="minute15"):
        
        regime_total = {}
        for days in self.target_days_list:
            data = self.fetch_all_ohlcv(days)
            regime_interval = {}
            for interval, df in data.items():
                threshold = self.dynamic_threshold(df=df, k=self.k_dict[interval])
                summary, result_df = self.analyze_reversion_vs_momentum(df=df, threshold=threshold)
                regime = self.classify_interval_regime(result_df=result_df)
                regime_interval[interval] = regime
                
            regime_total[str(days)] = regime_interval
        
        result_json = regime_total
        result_markerable = regime_total[anchor_days][anchor_interval]

        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "upbit-regime"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "regime"]
        params["result_markerable"] = result_markerable
        params["result_json"] = result_json
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["mod_member_seq"] = 0

        self.research_result_dao.insert_with_limit(params, 10000)
        
    def fetch_all_ohlcv(self, days=30):

        count = 200
        base_intervals = [
            "minute1", "minute3", "minute5",
            "minute10", "minute15", "minute30",
            "minute60", 
        ]
        data = {}
        for interval in base_intervals:
                
            end_dt = datetime.datetime.now()
            start_dt = end_dt - datetime.timedelta(days=days)
            
            df = self.upbit.set_ohlcvs(interval, days, count, start_dt, end_dt)
            data[interval] = df

        return data
    
    def resample_ohlcv(self, df, rule):

        df_resampled = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        return df_resampled
    
    def calc_indicators(self, df):

        self.upbit.set_df(df)

        self.upbit.set_atr()
        self.upbit.set_atr_ratio()
        self.upbit.set_atr_ratio_ma()
        self.upbit.set_adx()
        self.upbit.set_bollinger_width()

        return self.upbit.get_df().copy()
        
    def dynamic_threshold(self, df, k=0.5):
        window = min(14, len(df))
        atr = (df["high"] - df["low"]).rolling(window).mean()
        return (atr / df["close"]).mean() * k

    def analyze_reversion_vs_momentum(self, df, threshold=0.05, forward_window=5):
        """
        threshold: 큰 움직임 기준 (예: 5%)
        forward_window: 이후 몇 캔들 볼지

        future_ret: 
        """

        df = df.copy()
        df["ret"] = df["close"].pct_change()

        # 큰 상승 / 하락 구간
        df["event"] = 0
        df.loc[df["ret"] > threshold, "event"] = 1   # 등
        df.loc[df["ret"] < -threshold, "event"] = -1 # 락

        results = []
        for i in range(len(df) - forward_window):
            if df.iloc[i]["event"] != 0:
                future_ret = (
                    df.iloc[i+forward_window]["close"] / df.iloc[i]["close"] - 1
                ) # 수익률 = (미래가격/현재가격 )- 1
                results.append({
                    "event": df.iloc[i]["event"],
                    "future_ret": future_ret
                })
            
        if len(results) == 0:
            return None, pd.DataFrame()
        
        result_df = pd.DataFrame(results)
        summary = result_df.groupby("event")["future_ret"].mean()
        return summary, result_df
    
    def classify_interval_regime(self, result_df, min_samples=10):
        """
        result_df 기반으로 interval 성향 판단
        """

        if result_df is None or len(result_df) < min_samples:
            return "neutral"

        up = result_df[result_df["event"] == 1]["future_ret"]
        down = result_df[result_df["event"] == -1]["future_ret"]

        # 평균
        up_mean = up.mean() if len(up) > 0 else 0
        down_mean = down.mean() if len(down) > 0 else 0

        # 점수화
        # 회귀: 급등↓ + 급락↑
        reversion_score = (-up_mean) + (down_mean)

        # 모멘텀: 급등↑ + 급락↓
        momentum_score = (up_mean) + (-down_mean)

        # 판단
        if reversion_score > momentum_score:
            return "reversion"

        elif momentum_score > reversion_score:
            return "momentum"

        else:
            return "neutral"