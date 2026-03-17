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
        mid = ["minute10", "minute15", "minute30", "minute60"]
        macro = ["minute240", "day", "week"]

        micro_score = sum(interval_regimes[i] == "TREND" for i in micro)
        mid_score = sum(interval_regimes[i] == "TREND" for i in mid)
        macro_score = sum(interval_regimes[i] == "TREND" for i in macro)

        micro_trend = micro_score >= 4
        mid_trend = mid_score >= 4
        macro_trend = macro_score >= 4

        # -----------------
        # anchor timeframe
        # -----------------
        df = data[anchor_interval]
        row = df.iloc[-1]

        # 스퀴즈
        boll_mean = df["bollinger_width"].rolling(100).mean().iloc[-1]
        squeeze = row["bollinger_width"] < boll_mean * 0.7                  # 단순형
        # bw_percentile = df["bollinger_width"].rank(pct=True).iloc[-1]     # 시장 적응형
        # squeeze = bw_percentile < 0.2
        
        # 볼륨, 확장성, 변동성
        atr_expand = row["atr_ratio"] > row["atr_ratio_ma"]
        vol_mean = df["volume"].rolling(20).mean().iloc[-1]
        volume_expand = row["volume"] > vol_mean * 1.5
        volatility_expand = atr_expand and row["bollinger_width"] > boll_mean
        
        breakout_ready = (
            squeeze and
            row["atr_ratio"] > row["atr_ratio_ma"] and
            row["volume"] > vol_mean
        )

        # -----------------
        # market regime
        # 테스팅 하면서 빠져 나가는 구간, 케이스가 있는지 봐야한다. 
        # [여러 의미를 한 케이스에서 타게끔] 만드는 것이 아닌 최대한 [하나의 의미를 한 케이스에서 타게끔] 하여 모든 케이스를 가시화 것이 목적이다.
        # 방향성 말고 추세를 보는 것이 목적이다.
        # 매수기에선 하락 트렌드가 끝나는 지점에서 약매수를, 바닥 횡보 구간에서 약매집을, 추세 변환하여 올라가는 시점에 강매수를 하는 것을 목적으로 한다
        # 매도기에선 상승 트렌드가 끝나는 지점에서 약매도를, 천장 횡보 구간에서 약분산을, 추세 변환하여 떨어지는 시점에 전량매도를 하는 것을 목적으로 한다
        # 패턴 신뢰성과 역패턴 위험성을 장기간 봐야한다.
        # -----------------
        if not micro_trend and not mid_trend and not macro_trend:
            regime = "DEAD_RANGE"
            regime_score = 0
            
        elif micro_trend and not mid_trend and not macro_trend:
            regime = "RANGE"
            regime_score = 1
            
        elif mid_trend and volatility_expand and volume_expand:
            regime = "TREND_START"
            regime_score = 2

        elif mid_trend and not macro_trend:
            regime = "TREND"
            regime_score = 3

        elif mid_trend and macro_trend:
            regime = "STRONG_TREND"
            regime_score = 6

        elif not mid_trend and breakout_ready:
            regime = "BREAKOUT_SETUP"
            regime_score = 5

        elif not mid_trend and macro_trend:
            regime = "STILL_TREND"
            regime_score = 4

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
            "day",
            "week"
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
            df["close"].rolling(20).mean().diff().rolling(5).mean().iloc[-1]                   # 추세의 질
        ])
        
        trend_score = base_score + persistence_score  # max 6

        return "TREND" if trend_score >= 2 else "RANGE"