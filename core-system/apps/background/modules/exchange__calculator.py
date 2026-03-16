from background.modules.log import system_module_log
import numpy as np
import pandas as pd 

import datetime

class ExChangeCalculator():
    
    def __init__(self, df=None):
        self.log = system_module_log
        self.df = df
        self.future_direction_horizon = 12
        self.future_direction_standard_pct = 0.5 
        
    def get_df(self):
        return self.df
        
    def set_df(self, df):
        self.df = df
        return self.df
    
    def clear_df(self):
        self.df = pd.DataFrame()
    
    def get_ohlcv(self):
        # override on each exchange
        return 
    
    def set_ohlcv(self):
        # override on each exchange
        return 
    
    def set_ohlcvs(self, interval, days, count, from_, to_):

        max_call = int((days * 24 * 12) / count) + 2

        dfs = []
        for _ in range(max_call):
            df = self.get_ohlcv(
                interval=interval,
                date=to_.strftime("%Y-%m-%d %H:%M:%S"),
                count=count
            )
            if df is None or df.empty:
                break

            dfs.append(df)

            # 30일 이전이면 종료
            oldest_dt = df["datetime"].iloc[0]
            if oldest_dt <= from_:
                break

            # 다음 호출 기준점
            if interval == "minute1":
                to_ = oldest_dt - datetime.timedelta(minutes=1)
            elif interval == "minute3":
                to_ = oldest_dt - datetime.timedelta(minutes=3)
            elif interval == "minute5":
                to_ = oldest_dt - datetime.timedelta(minutes=5)
            elif interval == "minute10":
                to_ = oldest_dt - datetime.timedelta(minutes=10)
            elif interval == "minute15":
                to_ = oldest_dt - datetime.timedelta(minutes=15)
            elif interval == "minute30":
                to_ = oldest_dt - datetime.timedelta(minutes=30)
            elif interval == "minute60":
                to_ = oldest_dt - datetime.timedelta(hours=1)
            elif interval == "minute240":
                to_ = oldest_dt - datetime.timedelta(hours=4)
            elif interval == "day":
                to_ = oldest_dt - datetime.timedelta(days=1)
            elif interval == "week":
                to_ = oldest_dt - datetime.timedelta(days=7)
            elif interval == "month":
                to_ = oldest_dt - datetime.timedelta(days=31)

        # --- df 콘켓
        df_combined = (
            pd.concat(dfs)
            .drop_duplicates(subset="datetime")
            .sort_values("datetime")
            .reset_index(drop=True)
        )
        self.df = df_combined
        return self.df
    
    def set_all_features(self):

        methods = [
            getattr(self, m)
            for m in dir(self)
            if callable(getattr(self, m))
            and m.startswith("set_")
            and m not in ["set_ticker"]
            and m not in ["set_df"]
            and m not in ["set_ohlcv"]
            and m not in ["set_ohlcvs"]
            and m not in ["set_all_features"]
        ]
        for method in methods:
            try:
                method()

            except Exception as e:
                self.log.info(f"ExChangeCalculator Error, method : {method.__name__}, error : {str(e)} ")

        return self.get_df()
    
    def set_timestamp(self):
        self.df["timestamp"] = self.df["datetime"].astype("int64") // 10**9
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='s')
        return self.df
    
    def set_minute(self):
        if "timestamp" not in self.df.columns:
            self.set_timestamp()

        self.df['minute'] = self.df['timestamp'].dt.minute
        return self.df
    
    def set_hour(self):
        self.df['hour'] = self.df['datetime'].dt.hour
        return self.df
    
    def set_day(self):
        self.df['day'] = self.df['datetime'].dt.day
        return self.df
    
    def set_weekday(self):
        self.df['weekday'] = self.df['datetime'].dt.weekday
        return self.df
    
    def set_weekday_num(self):
        self.df['weekday_num'] = self.df["datetime"].dt.weekday
        return self.df
    
    def set_month(self):
        self.df['month'] = self.df['datetime'].dt.month
        return self.df
    
    def set_minute_of_day(self):
        self.df['minute_of_day'] = self.df['datetime'].dt.hour * 60 + self.df['datetime'].dt.minute
        return self.df
    
    def set_hour_sin(self):
        if "hour" not in self.df.columns:
            self.set_hour()
            
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour'] / 24)
        return self.df
    
    def set_hour_cos(self):
        if "hour" not in self.df.columns:
            self.set_hour()

        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour'] / 24)
        return self.df
    
    def set_weekday_sin(self):
        if "weekday" not in self.df.columns:
            self.set_weekday()

        self.df['weekday_sin'] = np.sin(2 * np.pi * self.df['weekday'] / 7)
        return self.df
    
    def set_weekday_cos(self):
        if "weekday" not in self.df.columns:
            self.set_weekday()

        self.df['weekday_cos'] = np.cos(2 * np.pi * self.df['weekday'] / 7)
        return self.df
    
    def set_day_of_month_sin(self):
        if "day" not in self.df.columns:
            self.set_day()

        self.df['day_of_month_sin'] = np.sin(2 * np.pi * self.df['day'] / 31)
        return self.df

    def set_day_of_month_cos(self):
        if "day" not in self.df.columns:
            self.set_day()

        self.df['day_of_month_cos'] = np.cos(2 * np.pi * self.df['day'] / 31)
        return self.df

    def set_month_sin(self):
        if "month" not in self.df.columns:
            self.set_month()
        self.df['month_sin'] = np.sin(2 * np.pi * self.df['month'] / 12)
        return self.df

    def set_month_cos(self):
        if "month" not in self.df.columns:
            self.set_month()
        self.df['month_cos'] = np.cos(2 * np.pi * self.df['month'] / 12)
        return self.df

    def set_minute_of_day_sin(self):
        if "minute_of_day" not in self.df.columns:
            self.set_minute_of_day()

        self.df['minute_of_day_sin'] = np.sin(2 * np.pi * self.df['minute_of_day'] / 1440)
        return self.df

    def set_minute_of_day_cos(self):
        if "minute_of_day" not in self.df.columns:
            self.set_minute_of_day()

        self.df['minute_of_day_cos'] = np.cos(2 * np.pi * self.df['minute_of_day'] / 1440)
        return self.df
    
    """
    Technical Indicator
    """
    def set_volume_ma5(self):
        self.df["volume_ma5"] = self.df["volume"].rolling(window=5).mean()
        return self.df
    
    def set_volume_ma20(self):
        self.df["volume_ma20"] = self.df["volume"].rolling(window=20).mean()  # 20분 이동 평균
        return self.df
    
    def set_volume_ratio(self):
        self.df["volume_ratio"] = self.df["volume"] / self.df["volume_ma20"]
        return self.df
    
    def set_obv(self):
        self.df["obv"] = (self.df["close"].diff() > 0).astype(int) * self.df["volume"]
        self.df["obv"] = self.df["obv"].cumsum()
        return self.df
    
    def set_vwap(self):
        self.df["cum_volume"] = self.df["volume"].cumsum()
        self.df["cum_vwap"] = (self.df["volume"] * (self.df["high"] + self.df["low"] + self.df["close"]) / 3).cumsum()
        self.df["vwap"] = self.df["cum_vwap"] / self.df["cum_volume"]
        return self.df
    
    def set_volume_volatility(self):
        self.df["volume_volatility"] = self.df["volume"].rolling(window=10).std()
        return self.df
    
    def set_volume_spike(self):
        self.df["volume_spike"] = self.df["volume"] > (self.df["volume_ma20"] * 2)
        return self.df
    
    def set_rsi(self):
        delta = self.df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df["rsi"] = 100 - (100 / (1 + rs))
        return self.df
    
    def set_macd(self):
        self.df["macd"] = self.df["close"].ewm(span=12, adjust=False).mean() - self.df["close"].ewm(span=26, adjust=False).mean()
        self.df["macd_signal"] = self.df["macd"].ewm(span=9, adjust=False).mean()
        return self.df

    def set_rsi_change(self):
        self.df['rsi_change'] = self.df['rsi'].astype(float).diff()
        return self.df
    
    def set_bollinger_partition(self):
        
        # Bollinger Band 위치를 8개 구간으로 나누기
        def bollinger_band_partition(row):
            if row["close"] >= row["band_upper"]:
                return 6
            elif row["close"] >= row["band_upper"] - row["stddev"]:
                return 5
            elif row["close"] >= row["band_mid"]:
                return 4
            elif row["close"] >= row["band_mid"] - row["stddev"]:
                return 3
            elif row["close"] >= row["band_lower"]:
                return 2
            elif row["close"] < row["band_lower"]:
                return 1
            else:
                return 0 # error

        self.df["band_mid"] = self.df["close"].rolling(window=20).mean()
        self.df["stddev"] = self.df["close"].rolling(window=20).std()
        self.df["band_upper"] = self.df["band_mid"] + (self.df["stddev"] * 2)
        self.df["band_lower"] = self.df["band_mid"] - (self.df["stddev"] * 2)
        self.df["bollinger_partition"] = self.df.apply(bollinger_band_partition, axis=1)
        return self.df
    
    def set_high_low_ratio(self): 
        self.df['high_low_ratio'] = self.df['high'].astype(float) / self.df['low'].astype(float)
        return self.df
        
    def set_close_open_ratio(self):
        self.df['close_open_ratio'] = self.df['close'].astype(float) / self.df['open'].astype(float)
        return self.df
        
    def set_daily_range(self):
        self.df['daily_range'] = (self.df['high'].astype(float) - self.df['low'].astype(float)) / self.df['close'].astype(float)
        return self.df
        
    def set_price_change_ratio(self):
        self.df['price_change_ratio'] = (self.df['close'].astype(float) - self.df['open'].astype(float)) / self.df['open'].astype(float)
        return self.df
        
    def set_rolling_volatility(self):
        self.df['rolling_volatility'] = self.df['close'].astype(float).pct_change().rolling(10).std()
        return self.df
        
    def set_close_above_ma5(self):
        self.df['close_above_ma5'] = (self.df['close'].astype(float) > self.df['close'].rolling(5).mean()).astype(int)
        return self.df
        
    def set_candle_body_size(self):
        self.df['candle_body_size'] = (self.df['close'].astype(float) - self.df['open'].astype(float)).abs()
        return self.df
        
    def set_upper_wick(self):
        self.df['upper_wick'] = self.df['high'].astype(float) - self.df[['open', 'close']].astype(float).max(axis=1)
        return self.df

    def set_lower_wick(self):
        self.df['lower_wick'] = self.df[['open', 'close']].astype(float).min(axis=1) - self.df['low'].astype(float)
        return self.df

    def set_wick_ratio(self):
        high = self.df['high'].astype(float)
        low = self.df['low'].astype(float)
        open_ = self.df['open'].astype(float)
        close = self.df['close'].astype(float)
        upper = high - open_.combine(close, max)
        lower = open_.combine(close, min) - low
        self.df['wick_ratio'] = (upper + lower) / (high - low + 1e-6)
        return self.df
        
    def set_volatility_1h(self):
        self.df['volatility_1h'] = self.df['close'].astype(float).pct_change().rolling(12).std()
        return self.df
        
    def set_gap_vs_30min_avg(self):
        shifted_close = self.df['close'].astype(float).shift(1)
        self.df['gap_vs_30min_avg'] = (self.df['open'].astype(float) - shifted_close) / shifted_close.rolling(6).mean()
        return self.df
        
    def set_bollinger_width(self):
        ma = self.df['close'].astype(float).rolling(20)
        std = ma.std()
        self.df['bollinger_width'] = 4 * std / ma.mean()
        return self.df

    def set_close_vs_ma12(self):
        self.df['close_vs_ma12'] = self.df['close'].astype(float) / self.df['close'].astype(float).rolling(12).mean()
        return self.df

    def set_close_vs_ma36(self):
        self.df['close_vs_ma36'] = self.df['close'].astype(float) / self.df['close'].astype(float).rolling(36).mean()
        return self.df
    
    def set_ema_diff_12_36(self):
        self.df['ema_diff_12_36'] = self.df['close'].astype(float).rolling(12).mean() - \
                                    self.df['close'].astype(float).rolling(36).mean()
        return self.df

    def set_momentum_5_20(self):
        self.df['momentum_5_20'] = self.df['close'].astype(float).pct_change(5) - \
                                   self.df['close'].astype(float).pct_change(20)
        return self.df
        
    def set_volatility_10_30_ratio(self):
        vol10 = self.df['close'].astype(float).pct_change().rolling(10).std()
        vol30 = self.df['close'].astype(float).pct_change().rolling(30).std()
        self.df['volatility_10_30_ratio'] = vol10 / (vol30 + 1e-6)
        return self.df
    
    def set_atr(self, period=14):

        high = self.df['high'].astype(float)
        low = self.df['low'].astype(float)
        close = self.df['close'].astype(float)

        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Wilder 방식 (EMA 기반)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        self.df['atr'] = atr
        return self.df

    def set_atr_ratio(self):
        if "atr" not in self.df.columns:
            self.set_atr()
            
        self.df['atr_ratio'] = self.df['atr'].astype(float) / self.df['close'].astype(float)
        return self.df
    
    def set_atr_ratio_ma(self):
        if "atr_ratio" not in self.df.columns:
            self.set_atr_ratio()

        self.df["atr_ratio_ma"] = self.df["atr_ratio"].ewm(span=20).mean()
        return self.df

    def set_adx(self, period=14):

        self.df["prev_close"] = self.df["close"].shift(1)
        self.df["prev_high"] = self.df["high"].shift(1)
        self.df["prev_low"] = self.df["low"].shift(1)

        # True Range
        self.df["tr"] = self.df[["high","low","prev_close"]].apply(
            lambda x: max(
                x["high"] - x["low"],
                abs(x["high"] - x["prev_close"]),
                abs(x["low"] - x["prev_close"])
            ),
            axis=1
        )

        # Directional movement
        self.df["+dm"] = self.df["high"] - self.df["prev_high"]
        self.df["-dm"] = self.df["prev_low"] - self.df["low"]

        self.df["+dm"] = self.df["+dm"].where((self.df["+dm"] > self.df["-dm"]) & (self.df["+dm"] > 0), 0)
        self.df["-dm"] = self.df["-dm"].where((self.df["-dm"] > self.df["+dm"]) & (self.df["-dm"] > 0), 0)

        # ATR
        self.df["atr"] = self.df["tr"].rolling(period).mean()

        # DI
        self.df["+di"] = 100 * (self.df["+dm"].rolling(period).mean() / self.df["atr"])
        self.df["-di"] = 100 * (self.df["-dm"].rolling(period).mean() / self.df["atr"])

        # DX
        self.df["dx"] = (abs(self.df["+di"] - self.df["-di"]) / (self.df["+di"] + self.df["-di"])) * 100

        # ADX
        self.df["adx"] = self.df["dx"].rolling(period).mean()

        return self.df
    
    def set_cdlengulfing(self):

        df = self.df.copy()
        prev_bearish = df['close'].shift(1) < df['open'].shift(1)
        prev_bullish = df['close'].shift(1) > df['open'].shift(1)

        engulf_bull = (
            prev_bearish &
            (df['close'] > df['open']) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1))
        )
        engulf_bear = (
            prev_bullish &
            (df['close'] < df['open']) &
            (df['open'] > df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1))
        )
        signal = pd.Series(np.where(engulf_bull, 100, np.where(engulf_bear, -100, 0)), index=df.index)
        self.df["cdlengulfing"] = signal
        return self.df

    def set_momentum(self, period=10):
        close = self.df['close'].astype(float)
        self.df['momentum'] = close - close.shift(period)
        return self.df

    def set_bullish_engulfing_flag(self):
        if "cdlengulfing" not in self.df.columns:
            self.set_cdlengulfing()

        if "momentum" not in self.df.columns:
            self.set_momentum()

        self.df['bullish_engulfing_flag'] = ((self.df['cdlengulfing'].astype(float)==1) & (self.df['momentum'].astype(float)>0)).astype(int)
        return self.df

    def set_bearish_engulfing_flag(self):
        if "cdlengulfing" not in self.df.columns:
            self.set_cdlengulfing()
            
        if "momentum" not in self.df.columns:
            self.set_momentum()
            
        self.df['bearish_engulfing_flag'] = ((self.df['cdlengulfing'].astype(float)==-1) & (self.df['momentum'].astype(float)<0)).astype(int)
        return self.df
    
    def set_price_zscore_20(self):
        close = self.df['close'].astype(float)
        mean20 = close.rolling(20).mean()
        std20  = close.rolling(20).std()
        self.df['price_zscore_20'] = (close - mean20) / (std20 + 1e-6)
        return self.df

    def set_volume_zscore_20(self):
        vol = self.df['volume'].astype(float)
        mean20 = vol.rolling(20).mean()
        std20  = vol.rolling(20).std()
        self.df['volume_zscore_20'] = (vol - mean20) / (std20 + 1e-6)
        return self.df

    def set_return_1_zscore_20(self):
        ret1 = self.df['close'].astype(float).pct_change(1)
        mean20 = ret1.rolling(20).mean()
        std20  = ret1.rolling(20).std()
        self.df['return_1_zscore_20'] = (ret1 - mean20) / (std20 + 1e-6)
        return self.df

    def set_ma36_slope_norm(self):
        ma36 = self.df['close'].astype(float).rolling(36).mean()
        slope = ma36.diff(5)  # 5-스텝 기울기
        atr = self.df['atr'].astype(float).replace(0, np.nan)
        self.df['ma36_slope_norm'] = slope / (atr + 1e-6)
        return self.df

    def set_trend_over_vol(self):
        # 단기-장기 차이를 변동성으로 정규화 (추세 대비 변동성)
        ema12 = self.df['close'].astype(float).ewm(span=12, adjust=False).mean()
        ema36 = self.df['close'].astype(float).ewm(span=36, adjust=False).mean()
        atr = self.df['atr'].astype(float)
        self.df['trend_over_vol'] = (ema12 - ema36) / (atr + 1e-6)
        return self.df

    def set_obv_ma_ratio_20(self):
        obv = self.df['obv'].astype(float)
        self.df['obv_ma_ratio_20'] = obv / (obv.rolling(20).mean() + 1e-6)
        return self.df

    def set_return_1d(self):
        self.df['return_1d'] = self.df['close'].astype(float).pct_change(288)
        
        # 5분봉 기준 288개 = 1일
        self.df['return_1d'] = self.df['close'].astype(float).pct_change(288)

        # 1. NaN 제거/보정
        self.df['return_1d'] = self.df['return_1d'].astype(float).replace([np.inf, -np.inf], np.nan)
        self.df['return_1d'] = self.df['return_1d'].astype(float).fillna(0)

        # 2. 극단값 클리핑 (예: -20% ~ +20% 범위)
        self.df['return_1d'] = self.df['return_1d'].astype(float).clip(lower=-0.2, upper=0.2)

        # 3. 표준화 (z-score)
        mean = self.df['return_1d'].astype(float).mean()
        std = self.df['return_1d'].astype(float).std() + 1e-6
        self.df['return_1d'] = (self.df['return_1d'].astype(float) - float(mean)) / float(std)
        return self.df

    def set_return_1h(self):
        self.df['return_1h'] = self.df['close'].astype(float).pct_change(12)
        return self.df

    def set_return_5h_mean(self):
        self.df['return_5h_mean'] = self.df['return_1h'].astype(float).rolling(5).mean()
        return self.df

    def set_volume_change(self):
        self.df['volume_change'] = self.df['volume'].astype(float).pct_change(288)
        return self.df

    def set_volume_ma_ratio(self):
        self.df['volume_ma_ratio'] = self.df['volume'].astype(float) / self.df['volume_ma20'].astype(float)
        return self.df
    
    def set_ichimoku_cloud(self):
        """
        tenkan_sen (전환선)
        (최근 9봉 최고가 + 최근 9봉 최저가) / 2

        kijun_sen (기준선)
        (최근 26봉 최고가 + 최근 26봉 최저가) / 2

        senkou_span_a (선행스팬 A)
        (tenkan_sen + kijun_sen) / 2
        → 26봉 미래로 shift

        senkou_span_b (선행스팬 B)
        (최근 52봉 최고가 + 최근 52봉 최저가) / 2
        → 26봉 미래로 shift

        chikou_span (후행스팬)
        현재 close → 26봉 과거로 shift
        """

        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        # 전환선 (Tenkan-sen)
        period9_high = high.rolling(window=9).max()
        period9_low = low.rolling(window=9).min()
        self.df["tenkan_sen"] = (period9_high + period9_low) / 2

        # 기준선 (Kijun-sen)
        period26_high = high.rolling(window=26).max()
        period26_low = low.rolling(window=26).min()
        self.df["kijun_sen"] = (period26_high + period26_low) / 2

        # 선행스팬 A (Senkou Span A)
        self.df["senkou_span_a"] = (
            (self.df["tenkan_sen"] + self.df["kijun_sen"]) / 2
        ).shift(26)

        # 선행스팬 B (Senkou Span B)
        period52_high = high.rolling(window=52).max()
        period52_low = low.rolling(window=52).min()
        self.df["senkou_span_b"] = (
            (period52_high + period52_low) / 2
        ).shift(26)

        # 후행스팬 (Chikou Span)
        self.df["chikou_span"] = close.shift(-26)

        return self.df
    
    def set_ichimoku_cloud_state(self):
        """
        cloud_top
        max(senkou_span_a, senkou_span_b)

        cloud_bottom
        min(senkou_span_a, senkou_span_b)

        above_cloud
        close > cloud_top

        below_cloud
        close < cloud_bottom

        inside_cloud
        cloud_bottom ≤ close ≤ cloud_top

        bull_cloud
        senkou_span_a > senkou_span_b

        bear_cloud
        senkou_span_a < senkou_span_b

        enter_bull_cloud
        enter_cloud == 1 AND bull_cloud == 1

        enter_bear_cloud
        enter_cloud == 1 AND bear_cloud == 1

        break_up_cloud
        이전: 구름 내부 또는 아래
        현재: 구름 위
        상승 돌파

        break_down_cloud
        이전: 구름 내부 또는 위
        현재: 구름 아래
        하락 돌파
        
        cloud_mid
        (senkou_span_a + senkou_span_b) / 2

        cloud_slope
        cloud_mid.diff()

        entry_cloud_slope
        enter_cloud 발생 시점의 cloud_slope
        """

        if "senkou_span_a" not in self.df.columns:
            self.set_ichimoku_cloud()

        cloud_top = self.df[["senkou_span_a","senkou_span_b"]].max(axis=1)
        cloud_bottom = self.df[["senkou_span_a","senkou_span_b"]].min(axis=1)

        # 가격 위치
        self.df["above_cloud"] = (self.df["close"] > cloud_top).astype(int)
        self.df["below_cloud"] = (self.df["close"] < cloud_bottom).astype(int)
        self.df["inside_cloud"] = (
            (self.df["close"] <= cloud_top) &
            (self.df["close"] >= cloud_bottom)
        ).astype(int)

        # 구름 방향
        self.df["bull_cloud"] = (self.df["senkou_span_a"] > self.df["senkou_span_b"]).astype(int)
        self.df["bear_cloud"] = (self.df["senkou_span_a"] < self.df["senkou_span_b"]).astype(int)

        prev_above = self.df["above_cloud"].shift(1)
        prev_below = self.df["below_cloud"].shift(1)
        prev_inside = self.df["inside_cloud"].shift(1)

        # 구름 진입
        self.df["enter_cloud"] = (
            (self.df["inside_cloud"] == 1) &
            (prev_inside == 0)
        ).astype(int)

        self.df["enter_bull_cloud"] = (
            (self.df["enter_cloud"] == 1) &
            (self.df["bull_cloud"] == 1)
        ).astype(int)

        self.df["enter_bear_cloud"] = (
            (self.df["enter_cloud"] == 1) &
            (self.df["bear_cloud"] == 1)
        ).astype(int)

        # 구름 돌파
        self.df["break_up_cloud"] = (
            (self.df["above_cloud"] == 1) &
            ((prev_inside == 1) | (prev_below == 1))
        ).astype(int)

        self.df["break_down_cloud"] = (
            (self.df["below_cloud"] == 1) &
            ((prev_inside == 1) | (prev_above == 1))
        ).astype(int)

        # 구름 중심선
        cloud_mid = (self.df["senkou_span_a"] + self.df["senkou_span_b"]) / 2
        self.df["cloud_mid"] = cloud_mid

        # 구름 기울기
        self.df["cloud_slope"] = cloud_mid.diff()

        # 진입 시점 기울기 기록
        self.df["entry_cloud_slope"] = (
            self.df["cloud_slope"]
            .where(self.df["enter_cloud"] == 1)
        )
        return self.df
    
    def set_ichimoku_cloud_position_state(self):
        """
        state	의미
        1	양운 위
        2	양운 내부 상단
        3	양운 내부 하단
        4	양운 아래
        5	음운 위
        6	음운 내부 상단
        7	음운 내부 하단
        8	음운 아래
        """

        if "senkou_span_a" not in self.df.columns:
            self.set_ichimoku_cloud()

        span_a = self.df["senkou_span_a"]
        span_b = self.df["senkou_span_b"]
        close = self.df["close"]

        cloud_top = self.df[["senkou_span_a","senkou_span_b"]].max(axis=1)
        cloud_bottom = self.df[["senkou_span_a","senkou_span_b"]].min(axis=1)
        cloud_mid = (span_a + span_b) / 2

        bull = span_a > span_b
        bear = span_a < span_b

        state = np.full(len(self.df), np.nan)

        # 양운
        state[(bull) & (close > cloud_top)] = 1
        state[(bull) & (close <= cloud_top) & (close > cloud_mid)] = 2
        state[(bull) & (close <= cloud_mid) & (close >= cloud_bottom)] = 3
        state[(bull) & (close < cloud_bottom)] = 4

        # 음운
        state[(bear) & (close > cloud_top)] = 5
        state[(bear) & (close <= cloud_top) & (close > cloud_mid)] = 6
        state[(bear) & (close <= cloud_mid) & (close >= cloud_bottom)] = 7
        state[(bear) & (close < cloud_bottom)] = 8

        self.df["cloud_position_state"] = state

        return self.df
    
    def set_ichimoku_cloud_break_state(self):
        """
        cloud_entry_price
        enter_cloud 발생 시 close

        bar_index
        0,1,2,3...

        cloud_entry_index
        enter_cloud 발생 bar_index

        duration
        현재 bar_index - cloud_entry_index

        cloud_break_slope
        (돌파 가격 - 진입 가격) / duration
        """

        if "enter_cloud" not in self.df.columns:
            self.set_ichimoku_cloud_state()
            
        # 구름 진입 가격 기록
        self.df["cloud_entry_price"] = self.df["close"].where(self.df["enter_cloud"] == 1)

        # forward fill로 현재 구름 구간의 진입 가격 유지
        self.df["cloud_entry_price"] = self.df["cloud_entry_price"].ffill()

        # 진입 index 기록
        self.df["bar_index"] = np.arange(len(self.df))

        self.df["cloud_entry_index"] = np.where(
            self.df["enter_cloud"] == 1,
            self.df["bar_index"],
            np.nan
        )

        self.df["cloud_entry_index"] = self.df["cloud_entry_index"].ffill()

        # 기간
        duration = self.df["bar_index"] - self.df["cloud_entry_index"]

        # slope 계산
        self.df["cloud_break_slope"] = (
            (self.df["close"] - self.df["cloud_entry_price"]) / duration
        )

        # 돌파 시점에서만 유효
        self.df["cloud_break_slope"] = self.df["cloud_break_slope"].where(
            (self.df["break_up_cloud"] == 1) | (self.df["break_down_cloud"] == 1)
        )
        
        # 퍼센티지 변화
        self.df["cloud_break_return"] = (
            (self.df["close"] - self.df["cloud_entry_price"]) /
            self.df["cloud_entry_price"]
        )

        # 기간
        duration = duration.replace(0, np.nan)

        # 퍼센티지 slope
        self.df["cloud_break_slope_pct"] = (self.df["cloud_break_return"] / duration * 100) 

        # 돌파 시점만 유지
        self.df["cloud_break_slope_pct"] = self.df["cloud_break_slope_pct"].where(
            (self.df["break_up_cloud"] == 1) |
            (self.df["break_down_cloud"] == 1)
        )
        return self.df
    
    """
    캔들스틱
    """
    def set_cdl2crows(self):
        df = self.df.copy()
        signal = (
            (df['close'].shift(2) > df['open'].shift(2)) &          # 2 전 양봉
            (df['open'].shift(1) > df['close'].shift(1)) &          # 1 전 음봉
            (df['open'].shift(1) < df['close'].shift(2)) &          # 1 전 시가 < 2 전 종가
            (df['close'].shift(1) > df['open'].shift(2)) &          # 1 전 종가 > 2 전 시가
            (df['open'] > df['close']) &                            # 현재 음봉
            (df['open'] < df['close'].shift(1)) &                   # 현재 시가 < 1 전 종가
            (df['close'] < df['close'].shift(1))                    # 현재 종가 < 1 전 종가  
        )
        
        self.df["cdl2crows"] = signal.astype(int) * -100
        return self.df

    def set_cdl3blackcrows(self):
        df = self.df.copy()
        signal = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['open'] < df['open'].shift(1)) &
            (df['open'].shift(1) < df['open'].shift(2)) &
            (df['close'] < df['close'].shift(1)) &
            (df['close'].shift(1) < df['close'].shift(2))
        )
        
        self.df["cdl3blackcrows"] = signal.astype(int) * -100
        return self.df

    def set_cdl3inside(self):
        df = self.df.copy()

        up = (
            (df['high'].shift(2) > df['high'].shift(1)) &
            (df['low'].shift(2) < df['low'].shift(1)) &
            (df['high'].shift(1) > df['high']) &
            (df['low'].shift(1) < df['low']) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'] > df['open'])
        )
        down = (
            (df['high'].shift(2) > df['high'].shift(1)) &
            (df['low'].shift(2) < df['low'].shift(1)) &
            (df['high'].shift(1) > df['high']) &
            (df['low'].shift(1) < df['low']) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'] < df['open'])
        )
        signal = (up | down) & df['close'].shift(2).notna()
        self.df["cdl3inside"] = signal.astype(int) * 100
        return self.df
    
    def set_cdl3linestrike(self):
        df = self.df.copy()
        signal = (
            (df['close'].shift(3) > df['open'].shift(3)) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open']) &
            (df['close'] < df['open'].shift(3))
        )
        self.df["cdl3linestrike"] = signal.astype(int) * -100
        return self.df

    def set_cdl3outside(self):
        df = self.df.copy()
        signal = (
            (df['high'].shift(2) < df['high'].shift(1)) &
            (df['low'].shift(2) > df['low'].shift(1)) &
            (df['high'].shift(1) < df['high']) &
            (df['low'].shift(1) > df['low']) &
            ((df['close'].shift(2) < df['open'].shift(2)) & (df['close'] > df['open'])) |
            ((df['close'].shift(2) > df['open'].shift(2)) & (df['close'] < df['open']))
        )
        self.df["cdl3outside"] = signal.astype(int) * 100
        return self.df

    def set_cdl3starsinsouth(self):
        df = self.df.copy()
        signal = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] < df['open']) &
            (df['open'].shift(2) > df['open'].shift(1)) &
            (df['open'].shift(1) > df['open']) &
            (df['close'].shift(2) > df['close'].shift(1)) &
            (df['close'].shift(1) > df['close'])
        )
        self.df["cdl3starsinsouth"] = signal.astype(int) * 100
        return self.df

    def set_cdl3whitesoldiers(self):
        df = self.df.copy()
        signal = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['open'] > df['open'].shift(1)) &
            (df['open'].shift(1) > df['open'].shift(2)) &
            (df['close'] > df['close'].shift(1)) &
            (df['close'].shift(1) > df['close'].shift(2))
        )
        self.df["cdl3whitesoldiers"] = signal.astype(int) * 100
        return self.df

    def set_cdlabandonedbaby(self):
        df = self.df.copy()
        doji = (abs(df['open'] - df['close']) <= ((df['high'] - df['low']) * 0.1))
        gap_down = df['low'].shift(1) > df['high']
        gap_up = df['high'].shift(1) < df['low']
        signal = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            doji.shift(1) & gap_down &
            (df['close'] > df['open']) & gap_up
        )
        self.df["cdlabandonedbaby"] = signal.astype(int) * 100
        return self.df

    def set_cdladvanceblock(self):
        df = self.df.copy()
        body1 = abs(df['close'].shift(2) - df['open'].shift(2))
        body2 = abs(df['close'].shift(1) - df['open'].shift(1))
        body3 = abs(df['close'] - df['open'])
        signal = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] > df['open']) &
            (df['close'].shift(2) < df['close'].shift(1)) &
            (df['close'].shift(1) < df['close']) &
            (body1 > body2) & (body2 > body3)
        )
        self.df["cdladvanceblock"] = signal.astype(int) * -100
        return self.df

    def set_cdlbelthold(self):
        df = self.df.copy()
        signal = (
            (df['open'] == df['low']) & (df['close'] > df['open']) |
            (df['open'] == df['high']) & (df['close'] < df['open'])
        )
        self.df["cdlbelthold"] = signal.astype(int) * np.where(df['close'] > df['open'], 100, -100)
        return self.df

    def set_cdlbreakaway(self):
        df = self.df.copy()
        # 단순화된 Breakaway 조건 (상승/하락 양방 가능)
        up = (
            (df['close'].shift(4) < df['open'].shift(4)) &
            (df['close'].shift(3) < df['open'].shift(3)) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open'])
        )
        down = (
            (df['close'].shift(4) > df['open'].shift(4)) &
            (df['close'].shift(3) > df['open'].shift(3)) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open'])
        )
        
        # signal: 1 for up, -1 for down, 0 for none
        signal = pd.Series(np.where(up, 1, np.where(down, -1, 0)), index=df.index)

        # 강도 부여: 시가 대비 양봉/음봉 여부에 따라 100 또는 -100 곱하기
        direction = np.where(df['close'] > df['open'], 100, -100)
        self.df["cdlbreakaway"] = signal.astype(int) * direction
        return self.df

    def set_cdlclosingmarubozu(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
        
        # 조건에 맞는 캔들: True/False Series
        signal = (upper_shadow <= (body * 0.05)) | (lower_shadow <= (body * 0.05))
        
        # True → 1, False → 0 으로 변환
        signal_int = signal.astype(int)
        
        # 봉의 방향에 따라 100 또는 -100 곱하기
        direction = np.where(df['close'] > df['open'], 100, -100)
        
        result = signal_int * direction
        
        self.df["cdlclosingmarubozu"] = pd.Series(result, index=df.index)
        return self.df

    def set_cdlconcealbabyswall(self):
        df = self.df.copy()
        # 매우 드문 형태로, 조건은 아래와 같이 단순화
        signal = (
            (df['open'].shift(3) > df['close'].shift(3)) &
            (df['open'].shift(2) > df['close'].shift(2)) &
            (df['high'].shift(1) < df['open'].shift(2)) &
            (df['low'].shift(1) > df['close'].shift(2)) &
            (df['high'] < df['open'].shift(1)) &
            (df['low'] > df['close'].shift(1))
        )
        self.df["cdlconcealbabyswall"] = signal.astype(int) * 100
        return self.df

    def set_cdlcounterattack(self):
        df = self.df.copy()
        signal = (
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open']) &
            (df['close'] == df['close'].shift(1))
        )
        self.df["cdlcounterattack"] = signal.astype(int) * 100
        return self.df

    def set_cdldarkcloudcover(self):
        df = self.df.copy()
        midpoint = (df['open'].shift(1) + df['close'].shift(1)) / 2
        signal = (
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['open'] > df['close']) &
            (df['open'] > df['high'].shift(1)) &
            (df['close'] < midpoint)
        )
        self.df["cdldarkcloudcover"] = signal.astype(int) * -100
        return self.df

    def set_cdldoji(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        signal = (body <= (df['high'] - df['low']) * 0.1)
        self.df["cdldoji"] = signal.astype(int) * 100
        return self.df

    def set_cdldojistar(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        prev_body = abs(df['close'].shift(1) - df['open'].shift(1))
        gap = df['low'] > df['high'].shift(1)
        doji = (body <= (df['high'] - df['low']) * 0.1)
        signal = (doji & gap & (prev_body > 0))
        self.df["cdldojistar"] = signal.astype(int) * 100
        return self.df

    def set_cdldragonflydoji(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
        signal = (
            (body <= (df['high'] - df['low']) * 0.1) &
            (upper_shadow <= (df['high'] - df['low']) * 0.1) &
            (lower_shadow >= (df['high'] - df['low']) * 0.5)
        )
        self.df["cdldragonflydoji"] = signal.astype(int) * 100
        return self.df

    def set_cdleveningdojistar(self):
        df = self.df.copy()
        doji = abs(df['close'].shift(1) - df['open'].shift(1)) <= (df['high'].shift(1) - df['low'].shift(1)) * 0.1
        signal = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            doji &
            (df['close'] < df['open']) &
            (df['close'] < (df['close'].shift(2) + df['open'].shift(2)) / 2)
        )
        self.df["cdleveningdojistar"] = signal.astype(int) * -100
        return self.df

    def set_cdleveningstar(self):
        df = self.df.copy()
        body2 = abs(df['close'].shift(1) - df['open'].shift(1))
        small_body = body2 < (df['high'].shift(1) - df['low'].shift(1)) * 0.2
        signal = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            small_body &
            (df['close'] < df['open']) &
            (df['close'] < (df['open'].shift(2) + df['close'].shift(2)) / 2)
        )
        self.df["cdleveningstar"] = signal.astype(int) * -100
        return self.df

    def set_cdlgapsidesidewhite(self):
        df = self.df.copy()
        cond = (
            (df['open'].shift(2) < df['close'].shift(2)) &
            (df['open'].shift(1) > df['high'].shift(2)) &
            (df['close'].shift(1) > df['high'].shift(2)) &
            (df['open'] > df['high'].shift(2)) &
            (df['close'] > df['high'].shift(2)) &
            (df['close'].shift(1) == df['close'])
        )
        self.df["cdlgapsidesidewhite"] = cond.astype(int) * 100
        return self.df

    def set_cdlgravestonedoji(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (body <= (df['high'] - df['low']) * 0.1) &
            (lower_shadow <= (df['high'] - df['low']) * 0.1) &
            (upper_shadow >= (df['high'] - df['low']) * 0.5)
        )
        self.df["cdlgravestonedoji"] = cond.astype(int) * 100
        return self.df

    def set_cdlhammer(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        lower = df[['close', 'open']].min(axis=1) - df['low']
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        
        cond = (lower > body * 2) & (upper < body)
        
        signal_int = cond.astype(int)
        direction = np.where(df['close'] > df['open'], 100, -100)
        
        result = signal_int * direction
        
        self.df["cdlhammer"] = pd.Series(result, index=df.index)
        return self.df

    def set_cdlhangingman(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        lower = df[['close', 'open']].min(axis=1) - df['low']
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        cond = (
            (lower > body * 2) &
            (upper < body) &
            (df['close'] < df['open'])  # 음봉
        )
        self.df["cdlhangingman"] = cond.astype(int) * -100
        return self.df

    def set_cdlharami(self):
        df = self.df.copy()
        prev_body = abs(df['close'].shift(1) - df['open'].shift(1))
        curr_body = abs(df['close'] - df['open'])

        cond = (
            (curr_body < prev_body) &
            (df['open'] > df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1))
        )
        reverse = (
            (curr_body < prev_body) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1))
        )

        # 시그널 값: cond → -100, reverse → 100, 그 외 → 0
        signal = pd.Series(np.where(cond, -100, np.where(reverse, 100, 0)), index=df.index)
        self.df["cdlharami"] = signal
        return self.df
    
    def set_cdlharamicross(self):
        df = self.df.copy()
        curr_body = abs(df['close'] - df['open'])
        prev_body = abs(df['close'].shift(1) - df['open'].shift(1))
        is_doji = curr_body <= (df['high'] - df['low']) * 0.1

        cond = (
            is_doji &
            (df['open'] > df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1)) &
            (prev_body > curr_body)
        )
        reverse = (
            is_doji &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (prev_body > curr_body)
        )

        signal = pd.Series(np.where(cond, -100, np.where(reverse, 100, 0)), index=df.index)
        self.df["cdlharamicross"] = signal
        return self.df

    def set_cdlhighwave(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        shadow = (df['high'] - df['low'])
        cond = (
            (body / shadow < 0.3) &
            (shadow > df['close'] * 0.03)
        )
        self.df["cdlhighwave"] = cond.astype(int) * 100
        return self.df

    def set_cdlhikkake(self):
        df = self.df.copy()
        inside_bar = (
            (df['high'].shift(1) < df['high'].shift(2)) &
            (df['low'].shift(1) > df['low'].shift(2))
        )
        breakout = (
            (df['high'] > df['high'].shift(1)) &
            (df['low'] > df['low'].shift(1))
        )
        cond = inside_bar & breakout
        self.df["cdlhikkake"] = cond.astype(int) * 100
        return self.df

    def set_cdlhikkakemod(self):
        df = self.df.copy()
        inside_bar = (
            (df['high'].shift(1) < df['high'].shift(2)) &
            (df['low'].shift(1) > df['low'].shift(2))
        )
        breakout = (
            (df['high'] > df['high'].shift(1)) &
            (df['low'] > df['low'].shift(1))
        )
        confirmation = df['close'] > df['close'].shift(1)
        cond = inside_bar & breakout & confirmation
        self.df["cdlhikkakemod"] = cond.astype(int) * 100
        return self.df

    def set_cdlhomingpigeon(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] < df['open']) &
            (df['open'] > df['open'].shift(1)) &
            (df['close'] > df['close'].shift(1)) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1))
        )
        self.df["cdlhomingpigeon"] = cond.astype(int) * 100
        return self.df

    def set_cdlidentical3crows(self):
        df = self.df.copy()
        cond = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (abs(df['close'] - df['close'].shift(1)) < 0.1 * df['close'].shift(1)) &
            (abs(df['close'].shift(1) - df['close'].shift(2)) < 0.1 * df['close'].shift(2))
        )
        self.df["cdlidentical3crows"] = cond.astype(int) * -100
        return self.df

    def set_cdlinneck(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # 음봉
            (df['open'] < df['low'].shift(1)) &
            (abs(df['close'] - df['low'].shift(1)) / df['low'].shift(1) < 0.003)
        )
        self.df["cdlinneck"] = cond.astype(int) * -100
        return self.df

    def set_cdlinvertedhammer(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        lower = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (upper > body * 2) &
            (lower < body) &
            (body < (df['high'] - df['low']) * 0.3)
        )
        self.df["cdlinvertedhammer"] = cond.astype(int) * 100
        return self.df

    def set_cdlkicking(self):
        df = self.df
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # 첫째 날 음봉
            (df['close'] > df['open']) &  # 둘째 날 양봉
            (df['open'] > df['close'].shift(1))  # 둘째 날 시가가 첫째 날 종가 위에서 시작
        )
        self.df["cdlkicking"] = cond.astype(int)
        return self.df

    def set_cdlkickingbylength(self):
        df = self.df.copy()
        body1 = abs(df['close'].shift(1) - df['open'].shift(1))
        body2 = abs(df['close'] - df['open'])
        gap = abs(df['open'] - df['close'].shift(1)) > (df['high'] - df['low']).rolling(3).mean()
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open']) &
            (body2 > body1) &
            gap
        )
        self.df["cdlkickingbylength"] = cond.astype(int) * 100
        return self.df

    def set_cdlladderbottom(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(4) < df['open'].shift(4)) &
            (df['close'].shift(3) < df['open'].shift(3)) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] > df['open']) &
            (df['close'] > df['close'].shift(1))
        )
        self.df["cdlladderbottom"] = cond.astype(int) * 100
        return self.df

    def set_cdllongline(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        range_ = df['high'] - df['low']
        avg_body = body.rolling(5).mean()
        avg_range = range_.rolling(5).mean()
        cond = (
            (body > avg_body * 1.5) &
            (range_ > avg_range * 1.5)
        )
        self.df["cdllongline"] =  np.where(df['close'] > df['open'], 100, -100) * cond.astype(int)
        return self.df

    def set_cdlmarubozu(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        lower = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (upper <= body * 0.05) &
            (lower <= body * 0.05)
        )
        self.df["cdlmarubozu"] =  np.where(df['close'] > df['open'], 100, -100) * cond.astype(int)
        return self.df

    def set_cdlhomingpigeon(self):
        df = self.df
        body1 = abs(df['close'].shift(1) - df['open'].shift(1))
        body2 = abs(df['close'] - df['open'])
        cond = (
            (body1 > 0) & (body2 > 0) &
            (df['close'] < df['open']) & (df['close'].shift(1) < df['open'].shift(1)) &  # 둘 다 음봉
            (df['open'] >= df['open'].shift(1)) & (df['close'] <= df['close'].shift(1))  # 두번째 캔들이 첫 캔들 몸통 안에 있음
        )
        self.df["cdlhomingpigeon"] =  cond.astype(int)
        return self.df

    def set_cdlidentical3crows(self):
        df = self.df
        cond = (
            (df['close'].shift(2) < df['open'].shift(2)) & (df['close'].shift(1) < df['open'].shift(1)) & (df['close'] < df['open']) &  # 모두 음봉
            (df['close'].shift(2) > df['close'].shift(1)) & (df['close'].shift(1) > df['close']) &  # 종가 하락 연속
            (abs(df['open'].shift(1) - df['close'].shift(2)) < (df['high'].shift(2) - df['low'].shift(2)) * 0.1) &  # 첫-둘 몸통 거의 일치
            (abs(df['open'] - df['close'].shift(1)) < (df['high'].shift(1) - df['low'].shift(1)) * 0.1)  # 둘-셋 몸통 거의 일치
        )
        self.df["cdlidentical3crows"] =  cond.astype(int)
        return self.df

    def set_cdlinneck(self):
        df = self.df
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # 첫 음봉
            (df['close'] > df['open']) &  # 두번째 양봉
            (abs(df['open'] - df['close'].shift(1)) < (df['high'] - df['low']) * 0.1) &  # 두번째 시가 ~ 첫번째 종가 근처
            (df['close'] > df['low'].shift(1)) & (df['close'] < df['open'].shift(1))  # 두번째 종가가 첫번째 저가 근처
        )
        self.df["cdlinneck"] =  cond.astype(int)
        return self.df

    def set_cdlinvertedhammer(self):
        df = self.df
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (body <= (df['high'] - df['low']) * 0.3) &  # 몸통 작음
            (upper_shadow >= body * 2) &  # 윗꼬리 길다
            (lower_shadow <= body * 0.3)  # 아래꼬리 짧다
        )
        self.df["cdlinvertedhammer"] =  cond.astype(int)
        return self.df

    def set_cdlkicking(self):
        df = self.df
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # 첫 음봉
            (df['close'] > df['open']) &  # 두번째 양봉
            (df['open'] > df['close'].shift(1)) &  # 두번째 시가가 첫번째 종가 위에서 시작
            (df['close'].shift(1) > df['open'].shift(1))  # 첫번째 캔들 종가가 시가 위(음봉 양봉 구분에 따라 다름)
        )
        self.df["cdlkicking"] =  cond.astype(int)
        return self.df

    def set_cdlkickingbylength(self):
        df = self.df
        body1 = abs(df['close'].shift(1) - df['open'].shift(1))
        body2 = abs(df['close'] - df['open'])
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # 첫 음봉
            (df['close'] > df['open']) &  # 두번째 양봉
            (body2 > body1) &  # 두번째 몸통이 첫번째보다 길다
            (df['open'] > df['close'].shift(1))  # 두번째 시가가 첫번째 종가 위에서 시작
        )
        self.df["cdlkickingbylength"] =  cond.astype(int)
        return self.df

    def set_cdlladderbottom(self):
        df = self.df
        body1 = abs(df['close'].shift(3) - df['open'].shift(3))
        body2 = abs(df['close'].shift(2) - df['open'].shift(2))
        body3 = abs(df['close'].shift(1) - df['open'].shift(1))
        body4 = abs(df['close'] - df['open'])
        cond = (
            (df['close'].shift(3) > df['open'].shift(3)) &  # 양봉
            (df['close'].shift(2) < df['open'].shift(2)) &  # 음봉
            (df['close'].shift(1) > df['open'].shift(1)) &  # 양봉
            (df['close'] > df['open']) &  # 양봉
            (body2 < body1) & (body2 < body4) & (body3 < body4)  # 가운데 음봉 작음
        )
        self.df["cdlladderbottom"] =  cond.astype(int)
        return self.df

    def set_cdllongleggeddoji(self):
        df = self.df
        body = abs(df['close'] - df['open'])
        upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
        lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (body <= (df['high'] - df['low']) * 0.1) &  # 몸통 매우 작음 (도지)
            (upper_shadow >= body * 2) &  # 긴 윗꼬리
            (lower_shadow >= body * 2)    # 긴 아랫꼬리
        )
        self.df["cdllongleggeddoji"] =  cond.astype(int)
        return self.df

    def set_cdllongline(self):
        df = self.df
        body = abs(df['close'] - df['open'])
        cond = (
            (body >= (df['high'] - df['low']) * 0.7)  # 몸통이 전체 캔들 길이의 70% 이상
        )
        self.df["cdllongline"] =  cond.astype(int)
        return self.df

    def set_cdlmarubozu(self):
        df = self.df
        body = abs(df['close'] - df['open'])
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        lower = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (upper <= body * 0.05) &
            (lower <= body * 0.05)
        )
        self.df["cdlmarubozu"] =  np.where(df['close'] > df['open'], 100, -100) * cond.astype(int)
        return self.df

    def set_cdlshortline(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        range_ = df['high'] - df['low']
        cond = (
            (body < range_ * 0.25) &
            (range_ < df['close'].rolling(5).mean() * 0.02)
        )
        self.df["cdlshortline"] =  np.where(df['close'] > df['open'], 100, -100) * cond.astype(int)
        return self.df

    def set_cdlspinningtop(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        lower = df[['close', 'open']].min(axis=1) - df['low']
        cond = (
            (body < (upper + lower)) &
            (upper > body * 0.5) &
            (lower > body * 0.5)
        )
        self.df["cdlspinningtop"] =  np.where(df['close'] > df['open'], 100, -100) * cond.astype(int)
        return self.df

    def set_cdlstalledpattern(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['open'].shift(1) > df['open'].shift(2)) &
            (df['open'] > df['open'].shift(1)) &
            (df['close'] < df['open'])
        )
        self.df["cdlstalledpattern"] = cond.astype(int) * -100
        return self.df

    def set_cdlsticksandwich(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open']) &
            (abs(df['close'] - df['close'].shift(2)) < 0.001 * df['close'])
        )
        self.df["dlsticksandwich"] = cond.astype(int) * 100
        return self.df

    def set_cdltakuri(self):
        df = self.df.copy()
        body = abs(df['close'] - df['open'])
        lower = df[['close', 'open']].min(axis=1) - df['low']
        upper = df['high'] - df[['close', 'open']].max(axis=1)
        cond = (
            (body < lower * 0.3) &
            (lower > body * 3) &
            (upper < body * 0.1)
        )
        self.df["cdltakuri"] = cond.astype(int) * 100
        return self.df

    def set_cdltasukigap(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['open'].shift(1) < df['low'].shift(2)) &  # gap down
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open']) &
            (df['open'] < df['close'].shift(1))
        )
        self.df["cdltasukigap"] = cond.astype(int) * 100
        return self.df

    def set_cdlthrusting(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['open'] < df['low'].shift(1)) &
            (df['close'] > df['low'].shift(1)) &
            (df['close'] < (df['open'].shift(1) + df['close'].shift(1)) / 2)
        )
        self.df["cdlthrusting"] = cond.astype(int) * -100
        return self.df

    def set_cdltristar(self):
        df = self.df.copy()
        is_doji = abs(df['close'] - df['open']) < (df['high'] - df['low']) * 0.1
        cond = (
            is_doji.shift(2) & is_doji.shift(1) & is_doji &
            (abs(df['open'].shift(1) - df['open'].shift(2)) > df['close'] * 0.01) &
            (abs(df['open'] - df['open'].shift(1)) > df['close'] * 0.01)
        )
        self.df["cdltristar"] = cond.astype(int) * 100
        return self.df

    def set_cdlunique3river(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['open'] < df['low'].shift(1)) &
            (df['close'] > df['close'].shift(1))
        )
        self.df["cdlunique3river"] = cond.astype(int) * 100
        return self.df

    def set_cdlupsidegap2crows(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['open'].shift(1) > df['high'].shift(2)) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['open'] > df['open'].shift(1)) &
            (df['close'] < df['close'].shift(1))
        )
        self.df["cdlupsidegap2crows"] = cond.astype(int) * -100
        return self.df

    def set_cdlxsidegap3methods(self):
        df = self.df.copy()
        cond = (
            (df['close'].shift(4) < df['open'].shift(4)) &  # 음봉
            (df['close'].shift(3) > df['open'].shift(3)) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['open'] < df['low'].shift(1)) &  # gap down
            (df['close'] < df['open'])
        )
        self.df["cdlxsidegap3methods"] = cond.astype(int) * -100
        return self.df

    """
    """
    def set_future_close(self):
        self.df["future_close"] = self.df["close"].shift(-self.future_direction_horizon)
        return self.df
    
    def set_future_change(self):
        if "future_close" not in self.df.columns:
            self.set_future_close()

        self.df["future_change"] = self.df["future_close"] - self.df["close"]
        return self.df
    
    def set_future_change_pct(self):
        if "future_change" not in self.df.columns:
            self.set_future_change()

        self.df["future_change_pct"] = (self.df["future_change"] / self.df["close"]) * 100
        return self.df
    
    def set_future_direction(self):
        if "future_change_pct" not in self.df.columns:
            self.set_future_change_pct()

        self.future_direction_standard_pct = 0.5 
        self.df["future_direction"] = self.df["future_change_pct"].apply(
            lambda x: "UP" if x > self.future_direction_standard_pct/100 \
                else ("DOWN" if x < -self.future_direction_standard_pct/100 \
                    else "FLAT")
        )
        return self.df
    
    def set_future_direction_num(self):
        if "future_change_pct" not in self.df.columns:
            self.set_future_change_pct()

        self.df["future_direction_num"] = self.df["future_change_pct"].apply(
            lambda x: 1 if x > 0 else (-1 if x < -0 else 0)
        )
        return self.df
    
    def set_signed_volume(self):
        if "future_direction_num" not in self.df.columns:
            self.set_future_direction_num()

        self.df["signed_volume"] = self.df["volume"] * self.df["future_direction_num"]
        return self.df
    
    def set_pos_volume(self):
        if "signed_volume" not in self.df.columns:
            self.set_signed_volume()

        self.df["pos_volume"] = self.df["signed_volume"].apply(lambda x: x if x > 0 else 0)
        return self.df
    
    def set_neg_volume(self):
        if "signed_volume" not in self.df.columns:
            self.set_signed_volume()

        self.df["neg_volume"] = self.df["signed_volume"].apply(lambda x: abs(x) if x < 0 else 0)
        return self.df
    
    def set_volume_imbalance(self):
        if "pos_volume" not in self.df.columns:
            self.set_pos_volume()

        if "neg_volume" not in self.df.columns:
            self.set_neg_volume()

        self.df["volume_delta"] = self.df["pos_volume"] - self.df["neg_volume"]

        self.df["volume_imbalance"] = (
            self.df["pos_volume"] - self.df["neg_volume"]
        ) / (
            self.df["pos_volume"] + self.df["neg_volume"] + 1e-9
        )
        return self.df
    
    