
import numpy as np
import pandas as pd 

class ExChangeCalculator():
    
    def __init__(self, df=None):
        self.df = df
    
    def clear_df(self):
        self.df = pd.DataFrame()
        
    def get_df(self):
        return self.df
    
    def set_ohlcv(self):
        # override on each exchange
        return 
    
    def set_hour_sin(self):
        self.df['hour'] = self.df['datetime'].dt.hour
        self.df['hour_sin'] = np.sin(2 * np.pi * self.df['hour'] / 24)
        return self.df
    
    def set_hour_cos(self):
        self.df['hour'] = self.df['datetime'].dt.hour
        self.df['hour_cos'] = np.cos(2 * np.pi * self.df['hour'] / 24)
        return self.df
    
    def set_weekday_sin(self):
        self.df['weekday'] = self.df['datetime'].dt.weekday
        self.df['weekday_sin'] = np.sin(2 * np.pi * self.df['weekday'] / 7)
        return self.df
    
    def set_weekday_cos(self):
        self.df['weekday'] = self.df['datetime'].dt.weekday
        self.df['weekday_cos'] = np.cos(2 * np.pi * self.df['weekday'] / 7)
        return self.df
    
    def set_day_of_month_sin(self):
        self.df['day'] = self.df['datetime'].dt.day
        self.df['day_of_month_sin'] = np.sin(2 * np.pi * self.df['day'] / 31)
        return self.df

    def set_day_of_month_cos(self):
        self.df['day'] = self.df['datetime'].dt.day
        self.df['day_of_month_cos'] = np.cos(2 * np.pi * self.df['day'] / 31)
        return self.df

    def set_month_sin(self):
        self.df['month'] = self.df['datetime'].dt.month
        self.df['month_sin'] = np.sin(2 * np.pi * self.df['month'] / 12)
        return self.df

    def set_month_cos(self):
        self.df['month'] = self.df['datetime'].dt.month
        self.df['month_cos'] = np.cos(2 * np.pi * self.df['month'] / 12)
        return self.df

    def set_minute_of_day_sin(self):
        self.df['minute_of_day'] = self.df['datetime'].dt.hour * 60 + self.df['datetime'].dt.minute
        self.df['minute_of_day_sin'] = np.sin(2 * np.pi * self.df['minute_of_day'] / 1440)
        return self.df

    def set_minute_of_day_cos(self):
        self.df['minute_of_day'] = self.df['datetime'].dt.hour * 60 + self.df['datetime'].dt.minute
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

    def set_rsi_change(self):
        self.df['rsi_change'] = self.df['rsi'].astype(float).diff()
        return self.df
        
    def set_volatility_10_30_ratio(self):
        vol10 = self.df['close'].astype(float).pct_change().rolling(10).std()
        vol30 = self.df['close'].astype(float).pct_change().rolling(30).std()
        self.df['volatility_10_30_ratio'] = vol10 / (vol30 + 1e-6)
        return self.df

    def set_atr_ratio(self):
        self.df['atr_ratio'] = self.df['atr'].astype(float) / self.df['close'].astype(float)
        return self.df

    def set_bullish_engulfing_flag(self):
        self.df['bullish_engulfing_flag'] = ((self.df['cdlengulfing'].astype(float)==1) & (self.df['momentum'].astype(float)>0)).astype(int)
        return self.df

    def set_bearish_engulfing_flag(self):
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
        return
    
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