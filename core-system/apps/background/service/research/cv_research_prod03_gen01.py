from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import numpy as np
import os

class CvResearchProd03Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd03Gen01
    Generation : 01 
    
    Desc : 
    - 박스캣
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
                self.resistance_zone()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def resistance_zone(self, anchor_interval="minute15"):
        """
        INSIDE_BOX        : 박스 내부
        AT_SUPPORT        : 지지 근처
        AT_RESISTANCE     : 저항 근처

        BREAKOUT_UP       : 위로 돌파
        BREAKOUT_DOWN     : 아래로 이탈

        FAKE_BREAKOUT_UP  : 위로 뚫었다가 다시 들어옴
        FAKE_BREAKOUT_DOWN: 아래로 뚫었다가 다시 들어옴

        NEW_BOX_UP        : 박스 상단 위에서 새 박스 형성
        NEW_BOX_DOWN      : 박스 하단 아래에서 새 박스 형성
        """

        df = self.fetch_ohlcv(anchor_interval)

        # 최근 구간만 사용 (중요)
        df = df.tail(200)

        supports, resistances = self.extract_support_resistance(df)

        current_price = df["close"].iloc[-1]

        # -----------------
        # 가장 가까운 박스 찾기
        # -----------------
        nearest_support = max([s for s in supports if s <= current_price], default=None)
        nearest_resistance = min([r for r in resistances if r >= current_price], default=None)

        # 박스 폭
        box_range = None
        if nearest_support and nearest_resistance:
            box_range = (nearest_resistance - nearest_support) / current_price

        # 상태 판단
        if nearest_support and nearest_resistance:
            if box_range < 0.03:
                zone_type = "TIGHT_RANGE"
            elif box_range < 0.08:
                zone_type = "RANGE"
            else:
                zone_type = "WIDE_RANGE"
        else:
            zone_type = "NO_BOX"
            
        state = self.detect_box_state(df, nearest_support, nearest_resistance)
        new_box_state = self.detect_new_box(df, nearest_support, nearest_resistance)

        final_state = new_box_state if new_box_state else state
        
        result_json = {
            "support_levels": supports,
            "resistance_levels": resistances,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "current_price": current_price,
            "box_range": box_range,
            "zone_type": zone_type,
            "box_state": final_state
        }

        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "upbit-sr-zone"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "support_resistance"]
        params["result_markerable"] = box_range if box_range else 0
        params["result_json"] = result_json
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["mod_member_seq"] = 0

        self.research_result_dao.insert_with_limit(params, 10000)
        
    def fetch_ohlcv(self, interval):

        self.upbit.set_ohlcv(interval=interval, count=300)
        return self.upbit.get_df().copy()
    
    def extract_support_resistance(self, df):

        swing_highs, swing_lows = self.find_swings(df)

        resistance = self.filter_levels(swing_highs, df)
        support = self.filter_levels(swing_lows, df)

        resistance = self.cluster_levels(resistance)
        support = self.cluster_levels(support)

        return support, resistance
    
    def find_swings(self, df, window=5):

        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i-window:i+window]):
                swing_highs.append(highs[i])

            if lows[i] == min(lows[i-window:i+window]):
                swing_lows.append(lows[i])

        return swing_highs, swing_lows
    
    def filter_levels(self, levels, df, tolerance=0.003):

        filtered = []
        close = df["close"]
        volume = df["volume"]

        for level in levels:
            touches = abs(close - level) / level < tolerance

            if touches.sum() >= 3:
                avg_vol = volume[touches].mean()
                if avg_vol > volume.mean():
                    filtered.append(level)

        return filtered
    
    def cluster_levels(self, levels, threshold=0.005):

        if not levels:
            return []

        levels = sorted(levels)
        clusters = [[levels[0]]]

        for lvl in levels[1:]:
            if abs(lvl - clusters[-1][-1]) / lvl < threshold:
                clusters[-1].append(lvl)
            else:
                clusters.append([lvl])

        return [float(np.mean(c)) for c in clusters]
    
    def detect_box_state(self, df, support, resistance):

        if not support or not resistance:
            return "NO_BOX"

        price = df["close"].iloc[-1]
        prev_price = df["close"].iloc[-2]

        box_height = resistance - support
        tolerance = box_height * 0.1  # 10% 범위

        # -----------------
        # 위치 판단
        # -----------------
        inside = support < price < resistance
        near_support = abs(price - support) < tolerance
        near_resistance = abs(price - resistance) < tolerance

        # -----------------
        # 돌파 / 이탈
        # -----------------
        breakout_up = price > resistance and prev_price <= resistance
        breakout_down = price < support and prev_price >= support

        # -----------------
        # 페이크
        # -----------------
        fake_up = prev_price > resistance and price < resistance
        fake_down = prev_price < support and price > support

        # -----------------
        # 상태 결정
        # -----------------
        if breakout_up:
            return "BREAKOUT_UP"

        elif breakout_down:
            return "BREAKOUT_DOWN"

        elif fake_up:
            return "FAKE_BREAKOUT_UP"

        elif fake_down:
            return "FAKE_BREAKOUT_DOWN"

        elif near_support:
            return "AT_SUPPORT"

        elif near_resistance:
            return "AT_RESISTANCE"

        elif inside:
            return "INSIDE_BOX"

        elif price > resistance:
            return "ABOVE_BOX"

        elif price < support:
            return "BELOW_BOX"

        return "UNKNOWN"
    
    def detect_new_box(self, df, support, resistance):

        # 최근 n개 캔들이 기존 박스 밖에서 유지되는지
        recent = df["close"].tail(10)

        if all(recent > resistance):
            return "NEW_BOX_UP"

        elif all(recent < support):
            return "NEW_BOX_DOWN"

        return None