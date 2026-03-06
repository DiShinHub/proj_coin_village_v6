from background.modules.log import system_module_log
from background.config.config import Config
from background.decorations.try_again import try_again
from background.decorations.cache_data import cache_data

from background.modules.exchange__calculator import ExChangeCalculator

from datetime import datetime, timedelta
import pandas as pd

class ExChangeBinance(ExChangeCalculator):
    
    def __init__(self):
        self.log = system_module_log
        config = Config()
        self.binance = config.set_binance()
        
        self.ticker = None
        self.ticker_org = None

    def set_ticker(self, ticker):
        self.ticker = ticker
        self.ticker_org = ticker.replace("USDT", "")
        return True

    def get_ticker(self):
        return self.ticker
    
    """
    prices & charts
    """
    @try_again(num=4)
    def get_ohlcv(self, interval="1d", date=None, count=100):
        """
        def description : 특정 interval의 Binance OHLCV 데이터 조회

        Parameters
        ----------
        interval : str
            캔들 간격 (기본값: '1d')
            ex) '1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M'
        date : str or datetime
            기준 날짜 (해당 시점까지 조회)
        count : int
            조회할 캔들 수

        Returns
        -------
        df : pandas.DataFrame
            OHLCV 데이터프레임
        """
        
        # Binance interval 맵핑 (pyupbit 스타일 대비)
        interval_map = {
            "minute1": "1m",
            "minute3": "3m",
            "minute5": "5m",
            "minute15": "15m",
            "minute30": "30m",
            "hour": "1h",
            "day": "1d",
            "week": "1w",
            "month": "1M"
        }
        interval = interval_map.get(interval, interval)

        # 기준 시점 계산
        if date:
            if isinstance(date, str):
                date = datetime.fromisoformat(date)

        # 데이터 조회
        klines = self.binance.get_klines(
            symbol=self.ticker,
            interval=interval,
            endTime=int(datetime.timestamp(date) * 1000) if date else None,
            limit=count,
        )
        return klines
        
    @try_again(num=4)
    def set_ohlcv(self, interval="1d", date=None, count=100):
        klines = self.get_ohlcv(interval, date, count)
        self.df = self.form_ohlcv(klines)
        return self.df
    
    def form_ohlcv(self, klines):
        
        # cv 공용 포맷으로 변경
        df = pd.DataFrame(klines, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])

        # ohlcv 추출
        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        
        # open_time → datetime 변환 
        df["datetime"] = pd.to_datetime(df["open_time"], unit="ms")
        #df["datetime"] = df["datetime"] + pd.Timedelta(hours=9) -> 한국시간으로 변환

        df.set_index("open_time", inplace=True)
        
        return df

        
        