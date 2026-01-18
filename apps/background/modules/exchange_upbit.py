from background.modules.log import system_module_log
from background.config.config import Config
from background.decorations.try_again import try_again
from background.decorations.cache_data import cache_data
from background.decorations.reuse_data import reuse_data

from background.modules.exchange__calculator import ExChangeCalculator

import pyupbit

from datetime import datetime, timedelta
import inspect

class ExChangeUpbit(ExChangeCalculator):

    def __init__(self):
        self.log = system_module_log
        config = Config()

        self.upbit = config.set_upbit()
        self.ticker = None
        self.ticker_org = None

    def set_ticker(self, ticker):
        self.ticker = ticker
        self.ticker_org = ticker.replace("KRW-", "")
        return True

    def get_ticker(self):
        return self.ticker
    
    """
    balance
    """
    @try_again(num=4)
    def get_KRW_tickers(self):
        """
        def description : 원화로 매매 가능한 코인 리스트

        Returns
        -------
        tickers : 티커 배열 (float)
        """
        tickers = pyupbit.get_tickers(fiat="KRW")
        return tickers
        
    @try_again(num=4)
    def get_krw_balance(self):
        """
        def description : 원화 잔고 조회

        Returns
        -------
        krw_balances : 원화
        """
        
        balances = self.upbit.get_balances()

        krw_balance = 0
        for balance in balances:
            if balance['currency'] == 'KRW':
                krw_balance = float(balance['balance'])

        return krw_balance

    @try_again(num=4)
    def get_ticker_balance(self):
        """
        def description : 특정 잔고 정보 조회

        Returns
        -------
        my_target_balance : 타겟 티커에 대한 잔고 정보
        """
        all_my_balance = self.get_all_my_balance()

        my_target_balance = 0
        for my_balance in all_my_balance:
            if my_balance["ticker"] == self.ticker_org:
                my_target_balance = float(my_balance["balance"])
                break

        return my_target_balance
    
    @try_again(num=4)
    def get_all_my_balance(self):
        """
        def description : 전체 잔고 정보 조회

        Returns
        -------
        balance_list : 잔고 딕셔너리 array
        """
        
        balances = self.upbit.get_balances()

        balance_dict = {}
        balance_list = []
        for b in balances:
            if b["balance"] is not None:
                balance_dict = {
                    "ticker": b["currency"],
                    "balance": float(b["balance"])
                }
                balance_list.append(balance_dict)

        return balance_list
    
    @try_again(num=4)
    def get_avg_price(self):
        """
        def description : 티커 평단 조회

        Returns
        -------
        avg_price : 평단
        """
        avg_price = self.upbit.get_avg_buy_price(self.ticker)
        return avg_price
    
    """
    trade 
    """
    @cache_data(ttl=1)
    @try_again(num=4)
    def buy_coin(self, krw_order):
        """
        def description : 코인 매수

        Parameters
        ----------
        krw_order : 코인 원화 주문 가격

        Returns
        -------
        boolean
        """
        
        fees = 0.0005
        buy_result = self.upbit.buy_market_order(
            self.ticker, krw_order * (1-fees))
        
        # 성공
        if "uuid" in buy_result:
            if "price" in buy_result:
                if "reserved_fee" in buy_result: 
                    return buy_result

        # 실패
        self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(buy_result)}")
        raise

    @cache_data(ttl=1)
    @try_again(num=4)
    def sell_coin(self, krw_order="All", current_price=None):
        """
        def description : 코인 매도
        

        Parameters
        ----------
        krw_order : 코인 원화 주문 가격

        Returns
        -------
        response_object : 결과 오브젝트(dict)
        """
        
        org_ticker = self.ticker

        # 전액 매도
        if krw_order == "all":
            self.ticker = self.ticker.replace("KRW-", "")
            ticker_balance = self.get_ticker_balance()
            self.ticker = org_ticker

            # 예외처리
            if krw_order > ticker_balance:
                self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : ticker 보유량이 부족합니다.")
                raise

        # 분할 매도
        else:
            ticker_balance = krw_order

        sell_result = self.upbit.sell_market_order(self.ticker, ticker_balance)

        # 매매 성공
        if "uuid" in sell_result:
            if "volume" in sell_result:
                if "reserved_fee" in sell_result: 
                    return sell_result

        # 실패
        self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(sell_result)}")
        raise
    
    """
    prices & charts
    """
    @try_again(num=4)
    def get_ohlcv(self, interval="day", date=None, count=100):
        
        ohlcv = None
        if date:
            ohlcv = pyupbit.get_ohlcv(self.ticker, interval=interval, to=self.adjust_date(date, interval), count=count)
            ohlcv["datetime"] = ohlcv.index
            
        else:
            ohlcv = pyupbit.get_ohlcv(self.ticker, interval=interval, count=count)
            ohlcv["datetime"] = ohlcv.index
        
        return ohlcv
    
    @try_again(num=4)
    def set_ohlcv(self, interval="day", date=None, count=100):
        self.df = self.get_ohlcv(interval, date, count)
        return self.df
    
    @try_again(num=4)
    def get_future_prices(self, date, days, interval):

        # 기준 시점 datetime으로 변환
        start_time = datetime.fromisoformat(date)

        # n일 뒤 날짜 계산
        end_date = (start_time + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        # pyupbit에서 필요한 데이터를 분 단위로 가져오기 (최소 데이터 확보)
        if interval == "minute5":
            count = int((1440/5)*days)

        elif interval == "minute15":
            count = int((1440/15)*days)

        elif interval == "minute30":
            count = int((1440/30)*days)

        elif interval == "minute60":
            count = int((1440/60)*days)

        else:
            self.log.info(f"{inspect.currentframe().f_code.co_name}, error : not allowed interval")
            return

        df = pyupbit.get_ohlcv(
            self.ticker, interval=interval, to=self.adjust_date(end_date, interval), count=count
        )

        # 기준 시점 이후 필요한 시간 간격 정의
        intervals = {
            "on_time": start_time,
            "after_15min": start_time + timedelta(minutes=15),
            "after_30min": start_time + timedelta(minutes=30),
            "after_1hour": start_time + timedelta(hours=1),
            "after_4hour": start_time + timedelta(hours=4),
            "after_12hour": start_time + timedelta(hours=12),
            "after_1day": start_time + timedelta(days=1),
            "after_2day": start_time + timedelta(days=2),
            "after_3day": start_time + timedelta(days=3),
            "after_4day": start_time + timedelta(days=4),
            "after_5day": start_time + timedelta(days=5),
            "after_6day": start_time + timedelta(days=6),
        }

        # 미래 종가 데이터를 저장할 딕셔너리
        future_prices = {}

        # 기준 시간 이후 데이터 필터링
        for label, target_time in intervals.items():
            try:
                # 가장 가까운 타임스탬프 찾기
                nearest_idx = df.index.get_indexer([target_time], method='backfill')[0]
                nearest_time = df.index[nearest_idx]
                future_prices[label] = df.loc[nearest_time, 'close']

            except KeyError:
                # 타임스탬프가 데이터 범위에 없을 경우 처리
                future_prices[label] = None

        return future_prices
    
    """
    additional
    """
    def adjust_date(self, date: str, interval: str) -> str:
        """
        def description : 날짜 보정
        upbit ohlcv 호출 시 날짜가 지정되는 경우 당일(당시간)의 데이터를 제외하기 때문에 인터벌 만큼 시간을 추가
        
        Parameters
        ----------
        
        date : 날짜
        interval : 인터벌
        
        Returns
        -------
        date_adjusted : 보정 된 날짜
        """
        
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        if interval == "minute1":
            dt += timedelta(minutes=1)
        elif interval == "minute3":
            dt += timedelta(minutes=3)
        elif interval == "minute5":
            dt += timedelta(minutes=5)
        elif interval == "minute10":
            dt += timedelta(minutes=10)
        elif interval == "minute15":
            dt += timedelta(minutes=15)
        elif interval == "minute30":
            dt += timedelta(minutes=30)
        elif interval == "minute60":
            dt += timedelta(hours=1)
        elif interval == "minute240":
            dt += timedelta(hours=4)
        elif interval == "day":
            dt += timedelta(days=1)
        elif interval == "week":
            dt += timedelta(weeks=1)
        elif interval == "month":
            year = dt.year + (dt.month // 12)
            month = dt.month % 12 + 1
            dt = datetime(year, month, 1)
        else:
            raise ValueError(f"Unknown interval: {interval}")

        date_adjusted = dt.strftime("%Y-%m-%d %H:%M:%S")
        return date_adjusted
    
    def get_price_diff_rate(self, from_price, to_price):
        """
        def description :가격 변화율 계산


        Parameters
        ----------
        from_price : 시작점 종가
        to_price : 종료점 종가

        Returns
        -------
        change_rate : 현재변화율 (float)
        """
        if from_price == 0 : 
            self.log.info(f"from_price가 0입니다.")
            raise
            
        if to_price == 0 : 
            self.log.info(f"to_price가 0입니다.")
            raise

        change_rate = ((to_price - from_price) / from_price) * 100
        change_rate = round(change_rate, 4)
        return change_rate