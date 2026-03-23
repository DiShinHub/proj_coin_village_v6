from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
import pandas as pd
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
            
            threshold = self.dynamic_threshold(df)
            summary, result_df = self.analyze_reversion_vs_momentum(df=df, threshold=threshold)
            regime = self.classify_interval_regime(result_df)
            self.log.info(f"regime of {self.ticker} {interval} : {regime}")
            # interval_regimes[interval] = self.calc_interval_regime(df, interval)
            #data[interval] = df

        # self.log.info(f"interval_regimes : {interval_regimes}")

        # df = data[anchor_interval]
        # row = df.iloc[-1]

        # # -----------------
        # # multi timeframe
        # # -----------------
        # micro = ["minute1", "minute3", "minute5"]
        # mid = ["minute10", "minute15", "minute30"]
        # macro = ["minute60", "minute240", "day"]

        # micro_score = sum(interval_regimes[i] == "TREND" for i in micro)
        # mid_score = sum(interval_regimes[i] == "TREND" for i in mid)
        # macro_score = sum(interval_regimes[i] == "TREND" for i in macro)

        # micro_trend = micro_score >= 2
        # mid_trend = mid_score >= 2
        # macro_trend = macro_score >= 2

        # # -----------------
        # # anchor timeframe
        # # -----------------
        # df = data[anchor_interval]
        # row = df.iloc[-1]

        # # 스퀴즈
        # # squeeze = row["bollinger_width"] < boll_mean * 0.7 
        
        # # 볼륨, 확장성, 변동성
        # boll_mean = df["bollinger_width"].rolling(100).mean().iloc[-1]
        # atr_expand = row["atr_ratio"] > row["atr_ratio_ma"]
        # vol_mean = df["volume"].rolling(20).mean().iloc[-1]
        # # volume_expand = row["volume"] > vol_mean * 1.5
        # # volatility_expand = atr_expand and row["bollinger_width"] > boll_mean
        
        # # 파생
        # re_activate = (
        #     atr_expand and
        #     row["volume"] > vol_mean
        # )
        # pullback = (
        #     row["close"] < df["close"].rolling(20).mean().iloc[-1]
        #     and not atr_expand
        # )
        # # was_squeeze = (
        # #     df["bollinger_width"].rolling(5).min().iloc[-2]
        # #     < boll_mean * 0.7
        # # )
        # # was_expansion = (
        # #     row["bollinger_width"] > df["bollinger_width"].iloc[-2]
        # # )
        # # breakout_setup = (
        # #     was_squeeze and
        # #     was_expansion and
        # #     atr_expand and
        # #     volume_expand
        # # )
        # # early_breakout = (
        # #     row["atr_ratio"] > row["atr_ratio_ma"] and
        # #     row["bollinger_width"] > df["bollinger_width"].rolling(20).mean().iloc[-1] * 0.9
        # # )
        # # early_trend_restart = (
        # #     re_accumulation and
        # #     early_breakout
        # # )
        
        # # switch
        # if not micro_trend and not mid_trend and not macro_trend:
        #     regime = "DEAD_RANGE"
        #     regime_score = 0
            
        # elif micro_trend and not mid_trend and not macro_trend:
        #     regime = "RANGE"
        #     regime_score = 1
            
        # # elif mid_trend and volatility_expand and volume_expand:
        # #     regime = "TREND_SETUP"
        # #     regime_score = 2

        # elif mid_trend and not macro_trend:
        #     regime = "WEEK_TREND"
        #     regime_score = 2

        # elif mid_trend and macro_trend:
        #     regime = "STRONG_TREND"
        #     regime_score = 4

        # elif not mid_trend and macro_trend:
            
        #     # # 트랜드 회귀
        #     # if early_trend_restart:
        #     #     regime = "TREND_RESTART"
        #     #     regime_score = 4.9
                
        #     # 재 축적
        #     if re_activate:
        #         regime = "RE_ACTIVATE"
        #         regime_score = 3.7

        #     # 쉬는 중
        #     elif pullback:
        #         regime = "PULLBACK"
        #         regime_score = 3.3

        #     # # 하락 전환 
        #     # elif breakout_setup:
        #     #     regime = "BREAKOUT_SETUP"
        #     #     regime_score = 4.1
            
        #     # 기타 
        #     else:
        #         regime = "STILL_TREND"
        #         regime_score = 3.5

        # else:
        #     regime = "UNKNOWN"
        #     regime_score = 999

        # result_json = {
        #     "market_regime": regime,
        #     "market_regime_score": regime_score,
        #     "interval_regimes": interval_regimes,
        #     "micro_trend": micro_trend,
        #     "mid_trend": mid_trend,
        #     "macro_trend": macro_trend
        # }

        # params = {}
        # params["runnable_service_seq"] = self.seq
        # params["type"] = "upbit-regime"
        # params["exchange"] = "upbit"
        # params["ticker"] = self.ticker
        # params["tags"] = ["upbit", "technical"]
        # params["result_markerable"] = regime_score
        # params["result_json"] = result_json
        # params["result_txt"] = ""
        # params["reg_member_seq"] = 0
        # params["mod_member_seq"] = 0
        # self.research_result_dao.insert_with_limit(params, 10000)
        
    def analyze_reversion_vs_momentum(self, df, threshold=0.05, forward_window=5):
        """
        threshold: 큰 움직임 기준 (예: 5%)
        forward_window: 이후 몇 캔들 볼지
        """

        df = df.copy()
        df['ret'] = df['close'].pct_change()

        # 큰 상승 / 하락 구간
        df['event'] = 0
        df.loc[df['ret'] > threshold, 'event'] = 1   # 급등
        df.loc[df['ret'] < -threshold, 'event'] = -1 # 급락

        results = []

        for i in range(len(df) - forward_window):
            if df.iloc[i]['event'] != 0:
                future_ret = (
                    df.iloc[i+forward_window]['close'] / df.iloc[i]['close'] - 1
                )
                results.append({
                    "event": df.iloc[i]['event'],
                    "future_ret": future_ret
                })

        if len(results) == 0:
            return None, pd.DataFrame()
        
        result_df = pd.DataFrame(results)
        summary = result_df.groupby('event')['future_ret'].mean()
        return summary, result_df
    
    def classify_interval_regime(self, 
                                 result_df,
                                min_samples=10,
                                threshold=0.0):
        """
        result_df 기반으로 interval 성향 판단
        """

        if result_df is None or len(result_df) < min_samples:
            return 'neutral'

        up = result_df[result_df['event'] == 1]['future_ret']
        down = result_df[result_df['event'] == -1]['future_ret']

        # 평균
        up_mean = up.mean() if len(up) > 0 else 0
        down_mean = down.mean() if len(down) > 0 else 0

        # 점수화
        # 회귀: 급등↓ + 급락↑
        reversion_score = (-up_mean) + (down_mean)

        # 모멘텀: 급등↑ + 급락↓
        momentum_score = (up_mean) + (-down_mean)

        # 판단
        if reversion_score > momentum_score + threshold:
            return 'reversion'

        elif momentum_score > reversion_score + threshold:
            return 'momentum'

        else:
            return 'neutral'
        
    def dynamic_threshold(self, df, k=2.0):
        window = min(14, len(df))
        atr = (df['high'] - df['low']).rolling(window).mean()
        # atr = (df['high'] - df['low']).rolling(14).mean()
        return (atr / df['close']).mean() * k

    def fetch_all_ohlcv(self):

        base_intervals = [
            "minute1", "minute3", "minute5",
            "minute10", "minute15", "minute30",
            "minute60", "minute240",
            "day"
        ]

        data = {}

        for interval in base_intervals:
            self.upbit.set_ohlcv(interval=interval, count=500)
            self.upbit.set_atr()
            self.upbit.set_atr_ratio()
            self.upbit.set_atr_ratio_ma()
            self.upbit.set_adx()
            self.upbit.set_bollinger_width()

            data[interval] = self.upbit.get_df().copy()

        day_df = data["day"].copy()
        resample_map = {
            "2day": "2D",
            "3day": "3D",
            "4day": "4D",
            "5day": "5D",
            "6day": "6D",
            "1week": "1W",
            "2week": "2W",
            "3week": "3W",
            "4week": "4W",
            "8week": "8W",
            "2month": "2M",
            "3month": "3M",
            "6month": "6M",
        }

        for name, rule in resample_map.items():
            df_resampled = self.resample_ohlcv(day_df, rule)
            df_resampled = self.calc_indicators(df_resampled)

            data[name] = df_resampled

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

    def calc_interval_regime(self, df, interval):

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
        
        # interval별 기준
        if interval in ["minute1", "minute3", "minute5"]:
            threshold = 3

        elif interval in ["minute10", "minute15", "minute30", "minute60"]:
            threshold = 4

        elif interval in ["minute240", "day"]:
            threshold = 4

        elif "day" in interval or "week" in interval:
            threshold = 5

        elif "month" in interval:
            threshold = 5
            
        is_trend = (base_score + persistence_score >= threshold)

        return "TREND" if is_trend else "RANGE"