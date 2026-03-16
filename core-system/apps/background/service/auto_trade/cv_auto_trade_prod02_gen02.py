from background.middlewares.service_handler import ServiceHandler
from background.middlewares.orderbook_handler import OrderbookHandler
from background.constance.upbit_constance import UpbitConst

from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.functions.common_function import generate_now_date

from background.dao.research_result_dao import ResearchResultDao
from background.dao.trade_result_dao import TradeResultDao



from background.decorations.transaction_lock import *

import multiprocessing
import datetime
import os
    

class CvAutoTradeProd02Gen02(OrderbookHandler, ServiceHandler):
    """
    Service Name : CvAutoTradeProd02
    Generation : 01 
    
    Desc : 
    - 저점 매수
    """

    slack_post_prefix = ":owl:"

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):

        OrderbookHandler.__init__(self, orderbook_key=UpbitConst.ORDERBOOK_QUEUE_KEY)
        ServiceHandler.__init__(self, schedule_options=schedule_options, interval_options=interval_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        
        self.order_intensities = self.service_options.get("order_intensities")
        self.order_max = self.service_options.get("order_max")
        self.paper_trading = self.service_options.get("paper_trading")
    
    def main(self):

        try:
            super().monitoring_order_books()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    @wait_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def execute_core_process(self, ticker, key):
        """
        def description : 코어 프로세스 실행
        """
        
        # --- 주문 강도 파싱
        order_intensity = self.order_intensities.get(ticker)
        
        # --- 호가 정보 추출
        order_book = self.redis.get_json_data(key) 

        # --- 실행
        cv_auto_trader_s2_gen02_main = CvAutoTradeProd02Gen02Core(self.seq, ticker, order_book, order_intensity, self.order_max, self.paper_trading)
        p = multiprocessing.Process(target=cv_auto_trader_s2_gen02_main.run)
        p.start()
        
        # --- 트래픽 제어 
        time.sleep(0.25)
        

class CvAutoTradeProd02Gen02Core():
    slack_post_prefix = ":owl:"
    
    def __init__(self, seq, ticker, order_book, order_intensity, order_max, paper_trading=False):
        
        self.log = Log(os.path.basename(__file__)).get_logger()
        #self.trade_result_dao = TradeResultDao()
        self.seq = seq
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        self.research_result_dao = ResearchResultDao()
        self.trade_result_dao = TradeResultDao()

        self.upbit.set_ticker(ticker)
        self.upbit.set_paper_trading(paper_trading)

        # --- 주입 값
        self.ticker = ticker
        self.order_intensity = order_intensity
        self.order_book = order_book
        self.order_max = order_max
        
        # --- 유동 값
        self.current_price = None             # 현재가
        self.close_price_list = []            # 종가 리스트
        self.bbbb_price = None                # bbbb가격
        self.bbbb_status = None               # bbbb상태
        self.bollinger_state_prev = None      # 이전 볼린저 상태 값
        self.bollinger_state_crr = None       # 현재 볼린저 상태 값
        self.order_seed = 0                   # 주문 시드
        self.order_amount = 0                 # 주문 비중
        self.order_hurdle = 0                 # 주문 허들
        self.order_last_dt = None             # 마지막 주문 시간
        self.regime = None
        self.regime_score = None
        
        # --- prefixes
        self.pref_bbbb_price = f"night_owl2s_bundle_bbbb_price_{self.ticker}"            # bbbb 가격 
        self.pref_bbbb_status = f"night_owl2s_bundle_bbbb_status_{self.ticker}"          # bbbb 상태 
        self.pref_bollinger_state = f"night_owl2s_bundle_bollinger_state_{self.ticker}"  # 볼린저 상태 
        self.pref_order_amount = f"night_owl2s_bundle_order_amount_{self.ticker}"        # 주문량 
        self.pref_order_hurdle = f"night_owl2s_bundle_order_hurdle_{self.ticker}"        # 주문 허들 
        self.pref_order_last_dt = f"night_owl2s_bundle_order_last_dt_{self.ticker}"      # 마지막 주문 시간

        self.pref_regime_score = f"night_owl2s_bundle_regime_score_{self.ticker}"  
        self.pref_regime = f"night_owl2s_bundle_regime_{self.ticker}"        

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def run(self):
    
        try:
            # 데이터 셋팅
            self.set_order_intensity()
            self.set_order_standard()
            self.set_order_decision_point()

            # BBBB mornitoring 
            if self.bbbb_status != "on_bbbb":
                self.off_bbbb()
                
            else:
                self.on_bbbb()
        
        except Exception as e:
            self.log.info(f"{str(e)}")
    
    """
    pre process
    """
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def set_order_intensity(self):
        
        self.order_percent_iv = self.order_intensity["order_percent_iv"]
        self.order_percent_ir = self.order_intensity["order_percent_ir"]
        self.order_hurdle_iv = self.order_intensity["order_hurdle_iv"]
        self.order_hurdle_ir = self.order_intensity["order_hurdle_ir"]
        self.order_reset_hours_if_stable = self.order_intensity.get("order_reset_hours_if_stable")

        if self.order_percent_iv: self.order_percent_iv = float(self.order_percent_iv)
        else:  
            raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_percent_iv")

        if self.order_percent_ir: self.order_percent_ir = float(self.order_percent_ir) 
        else: 
            raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_percent_ir")

        if self.order_hurdle_iv: self.order_hurdle_iv = float(self.order_hurdle_iv)
        else: 
            raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_hurdle_iv") 

        if self.order_hurdle_ir: self.order_hurdle_ir = float(self.order_hurdle_ir)
        else: 
            raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_hurdle_ir")

        if self.order_reset_hours_if_stable: self.order_reset_hours_if_stable = float(self.order_reset_hours_if_stable)
        else: 
            self.order_reset_hours_if_stable = 24
        
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def set_order_standard(self):
    
        self.bbbb_price = self.redis.hget_data(self.pref_bbbb_price, self.ticker)                   # bbbb 가격
        self.bbbb_status = self.redis.hget_data(self.pref_bbbb_status, self.ticker)                 # bbbb 상태
        self.bollinger_state_prev = self.redis.hget_data(self.pref_bollinger_state, self.ticker)    # 이전 볼린저 상태
        self.order_amount = self.redis.hget_data(self.pref_order_amount, self.ticker)               # 주문량
        self.order_hurdle = self.redis.hget_data(self.pref_order_hurdle, self.ticker)               # 주문 허들
        self.order_last_dt = self.redis.hget_data(self.pref_order_last_dt, self.ticker)             # 마지막 주문 시간
        
        if self.bbbb_price: self.bbbb_price = float(self.bbbb_price)
        else: self.bbbb_price = 0
        
        if self.bollinger_state_prev: self.bollinger_state_prev = int(self.bollinger_state_prev)
        else: self.bollinger_state_prev = 0

        if self.order_amount: self.order_amount = float(self.order_amount)
        else: self.order_amount = 0
        
        if self.order_hurdle: self.order_hurdle = float(self.order_hurdle)
        else:  self.order_hurdle = self.order_hurdle_iv
        
        if self.order_last_dt: self.order_last_dt = datetime.datetime.strptime(self.order_last_dt, "%Y-%m-%d %H:%M:%S")
        else: self.order_last_dt = datetime.datetime.now()


    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def set_order_decision_point(self):
        
        self.upbit.set_ohlcv(interval="minute5")
        self.upbit.set_bollinger_partition()
        self.upbit.set_rsi()
        self.upbit.set_rsi_change() 
        self.upbit.set_obv() 
        self.upbit.set_vwap() 
        df = self.upbit.get_df()

        self.current_price = float(df["close"].iloc[-1])
        self.bollinger_state_crr = int(df["bollinger_partition"].iloc[-1])
        self.bollinger_state_prev = int(df["bollinger_partition"].iloc[-2])
        self.close_price_list = [float(c) for c in df["close"].iloc[-10:].tolist()]

        res = self.research_result_dao.get(type="upbit-regime", ticker=self.ticker)
        if res:

            ### TEST START ###
            self.regime_score = self.redis.hget_data(self.pref_regime_score, self.ticker)      
            self.regime = self.redis.hget_data(self.pref_regime, self.ticker)         
            
            if self.regime_score != res.get("result_markerable"):
                self.redis.save_msg_on_Q(f"before regime_score {self.regime_score}")
                self.redis.save_msg_on_Q(f"befire regime {self.regime}")
                self.regime_score = res.get("result_markerable")
                self.regime = res.get("result_json").get("market_regime")
                self.redis.save_msg_on_Q(f"after regime_score {self.regime_score}")
                self.redis.save_msg_on_Q(f"after regime {self.regime}")

            self.regime_score = res.get("result_markerable")
            self.regime = res.get("result_json").get("market_regime")

            self.redis.hupd_date(self.pref_regime_score, self.ticker, self.regime_score)     
            self.redis.hupd_date(self.pref_regime, self.ticker, self.regime)     
            ### TEST END ###                
            


    """
    BBBB MORNITORING
    """
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def off_bbbb(self):

        # 하락세 감지, 모니터링 돌입
        if self.bollinger_state_crr == 1 and self.bollinger_state_prev == 1:
            self.pre_bbbb()
            
        # CASE 2: 매수 없이 상승세 감지      
        elif self.bollinger_state_crr in ([6]) and\
            self.bollinger_state_prev in ([5, 6]) and\
            datetime.timedelta(hours=self.order_reset_hours_if_stable) < (datetime.datetime.now()- self.order_last_dt):
            
            self.reset_order(f"{self.slack_post_prefix} : {self.ticker}의 상승세를 감지하였으며 {self.order_reset_hours_if_stable}시간 동안 거래를 감지하지 못하였습니다. 매매롤 초기화 합니다.")
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def pre_bbbb(self):
        
        # bbbb의 가격을 현재가로 잡고 bbbb 상태 변경
        self.redis.hupd_date(self.pref_bbbb_price, self.ticker, self.current_price) 
        self.redis.hupd_date(self.pref_bbbb_status, self.ticker, "on_bbbb")

        self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker}의 하단 무너짐이 감시 되었습니다. 모니터링을 시작합니다.")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def on_bbbb(self):
        
        # CASE 1: 매수 포인트 감지   
        """
        - 현재 볼린저 상태가 1(band_lower)이상
        - 이전 볼린저 상태가 1(band_lower)이상
        - 2봉 전 종가보다 전봉 종가가 커야함
        - bbbb당시 가격과 현재가의 변화율이 order_hurdle 이하여야함
        """
        if (self.bollinger_state_crr > 1 and\
            self.bollinger_state_prev > 1 and\
            self.close_price_list[-2] > self.close_price_list[-3] and\
            self.upbit.get_price_diff_rate(self.current_price, self.bbbb_price) > self.order_hurdle
            ): 

            self.order_seed = self.upbit.get_krw_balance()

            # 시드 제한
            if self.order_seed > self.order_max:
                self.order_seed = self.order_max

            # 주문액 최초 설정 (시드의 n%만큼 매수)
            if not self.order_amount:
                self.order_amount = self.order_seed * self.order_percent_iv * 0.01
                if self.order_amount < 5000: # 최소 시드 설정
                    self.order_amount = 5000

            # CASE 1-1 : 한화 없음
            if self.order_seed <= 5000:
                self.reset_order(f"{self.slack_post_prefix} : {self.ticker}를 매수하기 위한 한화가 없습니다. 초기화합니다.")

            # CASE 1-2 : 매수시도액보다 한화량 낮음. 초기화
            elif self.order_seed < self.order_amount:
                self.reset_order(f"{self.slack_post_prefix} : {self.ticker}을 매수하기 위한 한화가 부족합니다. 초기화합니다.")
            
            # CASE 1-3 : 정상 케이스, 매수
            else:
                self.post_bbbb()

        # CASE 2: 매수 없이 상승세 감지      
        elif self.bollinger_state_crr in ([6]) and\
            self.bollinger_state_prev in ([5, 6]):
            self.reset_bbbb(f"{self.slack_post_prefix} : {self.ticker}의 상승세를 감지하였습니다. 모니터링을 중단합니다.")
    

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def post_bbbb(self):

        self.redis.save_msg_on_Q(f"{self.regime}")
        self.log.info(f"self.regime : {self.regime}")

        self.log.info(f"df : ")
        df = self.upbit.get_df()
        for row in df.tail(10).to_dict(orient="records"):
            for k, v in row.items():
                self.log.info(f"{k}: {v}")
            self.log.info("-" * 40)

        # 매매 진행
        order_dt = str(generate_now_date())
        buy_result = self.upbit.buy_coin(self.order_amount)
        if buy_result:
            params = {
                "exchange": "upbit",
                "ticker": self.ticker,
                "uuid": buy_result.get("uuid"),
                "ord_side": buy_result.get("side"),
                "ord_type": buy_result.get("ord_type"),
                "price": buy_result.get("price"),
                "reserved_fee": buy_result.get("reserved_fee"),
                "remaining_fee": buy_result.get("remaining_fee"),
                "paid_fee": buy_result.get("paid_fee"),
                "state": buy_result.get("state"),
                "locked": buy_result.get("locked"),
                "executed_volume": buy_result.get("executed_volume"),
                "runnable_service_seq": self.seq
            }
            self.trade_result_dao.insert(params)

            # 메세지 포스트
            self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker}의 매수를 성공하였습니다.\n 주문가 : {round(float(buy_result['price']), 2)}, 수수료 : {round(float(buy_result['reserved_fee']))}\n\n")

            # 매매 기록 및 강도 올림
            if self.redis.hget_data(self.pref_bbbb_price, self.ticker):
                self.redis.hupd_date(self.pref_bbbb_status, self.ticker, "off_bbbb")                  
                self.redis.hupd_date(self.pref_order_amount, self.ticker, (self.order_amount * self.order_percent_ir)) 
                self.redis.hupd_date(self.pref_order_hurdle, self.ticker, (self.order_hurdle * self.order_hurdle_ir))  
                self.redis.hupd_date(self.pref_order_last_dt, self.ticker, order_dt) 

    """
    BBBB reset
    """
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def reset_bbbb(self, msg):
        
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_bbbb_status, self.ticker)
        self.redis.hdel_data(self.pref_bollinger_state, self.ticker)
        
        self.redis.save_msg_on_Q(msg)
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def reset_order(self, msg):
        
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_bbbb_status, self.ticker)
        self.redis.hdel_data(self.pref_bollinger_state, self.ticker)
        self.redis.hdel_data(self.pref_order_amount, self.ticker)
        self.redis.hdel_data(self.pref_order_hurdle, self.ticker)
        self.redis.hdel_data(self.pref_order_last_dt, self.ticker)
        
        self.redis.save_msg_on_Q(msg)