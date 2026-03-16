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
    
    def decide_regime(self, anchor_interval="minute5"):

        anchor_interval = "minute5"
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

        micro_trend = micro_score >= 2
        mid_trend = mid_score >= 2
        macro_trend = macro_score >= 2

        # -----------------
        # anchor timeframe
        # -----------------
        df = data[anchor_interval]
        row = df.iloc[-1]

        boll_mean = df["bollinger_width"].rolling(100).mean().iloc[-1]
        squeeze = row["bollinger_width"] < boll_mean * 0.7

        atr_expand = row["atr_ratio"] > row["atr_ratio_ma"]

        vol_mean = df["volume"].rolling(20).mean().iloc[-1]
        volume_expand = row["volume"] > vol_mean * 1.5

        volatility_expand = atr_expand and row["bollinger_width"] > boll_mean

        # -----------------
        # market regime
        # -----------------
        if not micro_trend and not mid_trend and not macro_trend:
            regime = "DEAD_RANGE"
            regime_score = 0

        elif squeeze and not mid_trend:
            regime = "BREAKOUT_SETUP"
            regime_score = 1

        elif mid_trend and macro_trend:
            regime = "SUPER_STRONG_TREND"
            regime_score = 6

        elif macro_trend:
            regime = "STRONG_TREND"
            regime_score = 5

        elif mid_trend and volatility_expand and volume_expand:
            regime = "TREND_START"
            regime_score = 4

        elif mid_trend and not macro_trend:
            regime = "TREND"
            regime_score = 3

        else:
            regime = "RANGE"
            regime_score = 2

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
        self.research_result_dao.upsert(params)

    """
    """
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

        trend_score = sum([
            row["bollinger_width"] > 0.04,
            row["atr_ratio"] > row["atr_ratio_ma"],
            row["adx"] > 25
        ])

        return "TREND" if trend_score >= 2 else "RANGE"