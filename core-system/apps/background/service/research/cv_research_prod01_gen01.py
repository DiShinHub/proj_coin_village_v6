from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import os

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
    
    def main(self):

        try:
            for ticker in self.tickers:
                
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.decide_regime()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def decide_regime(self, anchor_interval="minute15"):

        data = self.fetch_all_ohlcv()
        interval_regimes = {}
        for interval, df in data.items():
            interval_regimes[interval] = self.calc_interval_regime(df)
            data[interval] = df

        df = data[anchor_interval]
        row = df.iloc[-1]

        # -----------------
        # multi timeframe
        # -----------------
        micro = ["minute1", "minute3", "minute5"]
        mid = ["minute10", "minute15", "minute30"]
        macro = ["minute60", "minute240", "day"]

        micro_score = sum(interval_regimes[i] == "TREND" for i in micro)
        mid_score = sum(interval_regimes[i] == "TREND" for i in mid)
        macro_score = sum(interval_regimes[i] == "TREND" for i in macro)

        micro_trend = micro_score >= 2
        mid_trend = mid_score >= 2
        macro_trend = macro_score >= 2

        # -----------------
        # anchor timeframe
        # -----------------
        df = data[anchor_interval]
        row = df.iloc[-1]

        # 스퀴즈
        # squeeze = row["bollinger_width"] < boll_mean * 0.7 
        
        # 볼륨, 확장성, 변동성
        boll_mean = df["bollinger_width"].rolling(100).mean().iloc[-1]
        atr_expand = row["atr_ratio"] > row["atr_ratio_ma"]
        vol_mean = df["volume"].rolling(20).mean().iloc[-1]
        volume_expand = row["volume"] > vol_mean * 1.5
        volatility_expand = atr_expand and row["bollinger_width"] > boll_mean
        
        # 파생
        re_activate = (
            atr_expand and
            row["volume"] > vol_mean
        )
        # pullback = (
        #     row["close"] < df["close"].rolling(20).mean().iloc[-1]
        #     and not atr_expand
        # )
        # was_squeeze = (
        #     df["bollinger_width"].rolling(5).min().iloc[-2]
        #     < boll_mean * 0.7
        # )
        # was_expansion = (
        #     row["bollinger_width"] > df["bollinger_width"].iloc[-2]
        # )
        # breakout_setup = (
        #     was_squeeze and
        #     was_expansion and
        #     atr_expand and
        #     volume_expand
        # )
        # early_breakout = (
        #     row["atr_ratio"] > row["atr_ratio_ma"] and
        #     row["bollinger_width"] > df["bollinger_width"].rolling(20).mean().iloc[-1] * 0.9
        # )
        # early_trend_restart = (
        #     re_accumulation and
        #     early_breakout
        # )
        
        # switch
        if not micro_trend and not mid_trend and not macro_trend:
            regime = "DEAD_RANGE"
            regime_score = 0
            
        elif micro_trend and not mid_trend and not macro_trend:
            regime = "RANGE"
            regime_score = 1
            
        elif mid_trend and volatility_expand and volume_expand:
            regime = "TREND_SETUP"
            regime_score = 2

        elif mid_trend and not macro_trend:
            regime = "WEEK_TREND"
            regime_score = 3

        elif mid_trend and macro_trend:
            regime = "STRONG_TREND"
            regime_score = 5

        elif not mid_trend and macro_trend:
            
            # # 트랜드 회귀
            # if early_trend_restart:
            #     regime = "TREND_RESTART"
            #     regime_score = 4.9
                
            # 재 축적
            if re_activate:
                regime = "RE_ACTIVATE"
                regime_score = 4.7

            # # 쉬는 중
            # elif pullback:
            #     regime = "PULLBACK"
            #     regime_score = 4.3

            # # 하락 전환 
            # elif breakout_setup:
            #     regime = "BREAKOUT_SETUP"
            #     regime_score = 4.1
            
            # 기타 
            else:
                regime = "STILL_TREND"
                regime_score = 4.5

        else:
            regime = "UNKNOWN"
            regime_score = 999

        result_json = {
            "market_regime": regime,
            "market_regime_score": regime_score,
            "interval_regimes": interval_regimes,
            "micro_trend": micro_trend,
            "mid_trend": mid_trend,
            "macro_trend": macro_trend
        }

        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "upbit-regime"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "technical"]
        params["result_markerable"] = regime_score
        params["result_json"] = result_json
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["mod_member_seq"] = 0
        self.research_result_dao.insert_with_limit(params, 10000)
        
        # ### different version
        # weights = {
        #     # micro
        #     "minute1": 1,
        #     "minute3": 1,
        #     "minute5": 2,

        #     # mid
        #     "minute10": 2,
        #     "minute15": 3,
        #     "minute30": 3,
        #     "minute60": 4,

        #     # macro
        #     "minute240": 5,
        #     "day": 6,
        #     "week": 7
        # }
        
        # interval_scores = {}
        # for interval, regime in interval_regimes.items():
        #     if regime == "TREND":
        #         score = 1
            
        #     else:
        #         score = 0
                
        #     interval_scores[interval] =  score
            
        # total_score = 0
        # total_weight = 0
        # for interval, score in interval_scores.items():
        #     w = weights[interval]
        #     total_score += score * w
        #     total_weight += w

        # market_score = total_score / total_weight
        # if market_score >= 5:
        #     regime = "SUPER_STRONG_TREND"

        # elif market_score >= 4:
        #     regime = "STRONG_TREND"

        # elif market_score >= 3:
        #     regime = "TREND"

        # elif market_score >= 2:
        #     regime = "TREND_START"

        # else:
        #     regime = "RANGE"
        
        # 방향성 
        # direction_scores = {}
        # for interval, df in data.items():
        #     slope = df["close"].rolling(20).mean().diff().iloc[-1]
        #     direction_scores[interval] = 1 if slope > 0 else -1
        

        # 가중 방향
        # direction_total = 0
        # for interval in interval_scores:
        #     direction_total += direction_scores[interval] * weights[interval]

        # market_direction = "LONG" if direction_total > 0 else "SHORT"

    def fetch_all_ohlcv(self):

        intervals = [
            "minute1",
            "minute3",
            "minute5",
            "minute10",
            "minute15",
            "minute30",
            "minute60",
            "minute240",
            "day"
        ]

        data = {}
        for interval in intervals:

            self.upbit.set_ohlcv(interval=interval, count=120)
            self.upbit.set_atr()
            self.upbit.set_atr_ratio()
            self.upbit.set_atr_ratio_ma()
            self.upbit.set_adx()
            self.upbit.set_bollinger_width()

            data[interval] = self.upbit.get_df().copy()

        return data
        
    def calc_interval_regime(self, df):

        row = df.iloc[-1]

        # trend_score = sum([
        #     row["bollinger_width"] > 0.04,
        #     row["atr_ratio"] > row["atr_ratio_ma"],
        #     row["adx"] > 25
        # ])
        
        base_score = sum([
            row["adx"] > 25,                                                # 추세 강도
            row["atr_ratio"] > row["atr_ratio_ma"],                         # 변동성 확장
            df["close"].iloc[-1] > df["close"].rolling(20).mean().iloc[-1]  # 방향성
        ])
        
        persistence_score = sum([
            df["adx"].rolling(5).mean().iloc[-1] > 25,                                         # 지속성
            df["close"].rolling(5).mean().iloc[-1] > df["close"].rolling(20).mean().iloc[-1],  # 방향 유지
            (df["close"].rolling(20).mean().diff().rolling(5).mean().iloc[-1]) > 0             # 추세의 질
        ])
        
        trend_score = base_score + persistence_score  # max 6

        return "TREND" if trend_score >= 4 else "RANGE"