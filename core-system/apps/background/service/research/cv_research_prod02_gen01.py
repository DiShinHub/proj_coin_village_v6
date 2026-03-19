from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import os

class CvResearchProd02Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd02Gen01
    Generation : 01 
    
    Desc : 
    - 스눕 덕 
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
                self.decide_direction()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def decide_direction(self, anchor_interval="minute15"):

        data = self.fetch_all_ohlcv()
        interval_directions = {}

        for interval, df in data.items():
            interval_directions[interval] = self.calc_interval_direction(df)

        # -----------------
        # multi timeframe
        # -----------------
        micro = ["minute1", "minute3", "minute5"]
        mid = ["minute10", "minute15", "minute30"]
        macro = ["minute60", "minute240", "day"]

        def score_group(group):
            long_score = sum(interval_directions[i] == "LONG" for i in group)
            short_score = sum(interval_directions[i] == "SHORT" for i in group)
            return long_score, short_score

        micro_long, micro_short = score_group(micro)
        mid_long, mid_short = score_group(mid)
        macro_long, macro_short = score_group(macro)

        # -----------------
        # 최종 방향성 결정
        # -----------------
        long_total = micro_long + mid_long * 2 + macro_long * 3
        short_total = micro_short + mid_short * 2 + macro_short * 3

        if long_total - short_total >= 3:
            direction = "LONG"
            direction_score = long_total

        elif short_total - long_total >= 3:
            direction = "SHORT"
            direction_score = short_total * -1

        else:
            direction = "NEUTRAL"
            direction_score = 0

        result_json = {
            "market_direction": direction,
            "direction_score": direction_score,
            "interval_directions": interval_directions,
            "micro_long": micro_long,
            "mid_long": mid_long,
            "macro_long": macro_long,
            "micro_short": micro_short,
            "mid_short": mid_short,
            "macro_short": macro_short
        }

        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "upbit-direction"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "direction"]
        params["result_markerable"] = direction_score
        params["result_json"] = result_json
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["mod_member_seq"] = 0

        self.research_result_dao.insert_with_limit(params, 10000)

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

            data[interval] = self.upbit.get_df().copy()

        return data
    
    def calc_interval_direction(self, df):

        row = df.iloc[-1]

        ma20 = df["close"].rolling(20).mean()
        ma50 = df["close"].rolling(50).mean()

        # -----------------
        # 1. Trend slope
        # -----------------
        slope_short = ma20.diff().iloc[-1]
        slope_mid = ma50.diff().iloc[-1]

        # -----------------
        # 2. Price position
        # -----------------
        above_ma = row["close"] > ma20.iloc[-1]
        below_ma = row["close"] < ma20.iloc[-1]

        # -----------------
        # 3. Momentum / Pressure
        # -----------------
        atr_expand = row["atr_ratio"] > row["atr_ratio_ma"]

        vol_mean = df["volume"].rolling(20).mean().iloc[-1]
        volume_expand = row["volume"] > vol_mean * 1.3

        momentum_up = slope_short > 0 and slope_mid > 0
        momentum_down = slope_short < 0 and slope_mid < 0

        # -----------------
        # 4. Score
        # -----------------
        long_score = sum([
            momentum_up,
            above_ma,
            atr_expand,
            volume_expand
        ])

        short_score = sum([
            momentum_down,
            below_ma,
            atr_expand,
            volume_expand
        ])

        # -----------------
        # 5. Decision
        # -----------------
        if long_score >= 3 and long_score > short_score:
            return "LONG"

        elif short_score >= 3 and short_score > long_score:
            return "SHORT"

        else:
            return "NEUTRAL"