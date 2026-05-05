from background.middlewares.service_handler import ServiceHandler
from background.middlewares.orderbook_handler import OrderbookHandler
from background.constance.upbit_constance import UpbitConst

from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.functions.common_function import *

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
        self.seq = seq
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        self.minio = MinioModule()
        self.research_result_dao = ResearchResultDao()
        self.trade_result_dao = TradeResultDao()

        self.upbit.set_ticker(ticker)
        self.upbit.set_paper_trading(paper_trading)

        # --- 주입 값
        self.ticker = ticker
        self.order_intensity = order_intensity
        self.order_book = order_book
        self.order_max = order_max
        self.order_book_date = order_book.get("order_book_date", None)
        
        # --- 모드 설정
        self.cycle_state = None     
        self.after_bbbb_state = None                      
        
        # --- 유동 값
        self.current_price = None             # 현재가
        self.close_price_list = []            # 종가 리스트
        self.bbbb_price = None                # bbbb가격
        self.bollinger_state_prev = None      # 이전 볼린저 상태 값
        self.bollinger_state_crr = None       # 현재 볼린저 상태 값
        self.order_seed = 0                   # 주문 시드
        self.order_amount = 0                 # 주문 비중
        self.order_hurdle = 0                 # 주문 허들
        self.order_last_price = None          # 마지막 주문 가격
        self.order_last_dt = None             # 마지막 주문 시간

        # --- prefixes
        self.pref_service = str(self.__class__.__name__)
        self.pref_cycle_state = f"{self.pref_service}_{self.ticker}_cycle_state"                    # 사이클 상태
        self.pref_after_bbbb_state = f"{self.pref_service}_{self.ticker}_after_bbbb_state"          # after_bbbb_state 상태
        self.pref_bbbb_price = f"{self.pref_service}_{self.ticker}_bbbb_price"                      # bbbb 가격 
        self.pref_lowest_price = f"{self.pref_service}_{self.ticker}_lowest_price"                  # 특정 구역의 최저가
        self.pref_order_amount = f"{self.pref_service}_{self.ticker}_order_amount"                  # 주문량 
        self.pref_order_hurdle = f"{self.pref_service}_{self.ticker}_order_hurdle"                  # 주문 허들 
        self.pref_order_last_price = f"{self.pref_service}_{self.ticker}_order_last_price"          # 마지막 주문 시간
        self.pref_order_last_dt = f"{self.pref_service}_{self.ticker}_order_last_dt"                # 마지막 주문 시간
        
        self.pref_msg = f"{self.slack_post_prefix} [{self.ticker}] "
        
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def run(self):
        
        try:
            self.set_order_option()
            self.set_state_bucket()
            self.set_indicators()
        
            if self.cycle_state == "off_bbbb":
                self.off_bbbb()
                
            elif self.cycle_state == "on_bbbb":
                self.on_bbbb()
                
            elif self.cycle_state == "after_bbbb":
                
                if self.after_bbbb_state == "mornitoring_pivot_high":
                    self.after_bbbb_mornitoring_pivot_high()
                
                if self.after_bbbb_state == "mornitoring_pivot_low":
                    self.after_bbbb_mornitoring_pivot_low()
                
                elif self.after_bbbb_state == "mornitoring_stable":
                    self.after_bbbb_mornitoring_stable()
                
            elif self.cycle_state == "stable_bbbb":
                self.stable_bbbb()
                
            else:
                self.off_bbbb()
        
        except Exception as e:
            self.log.info(f"{str(e)}")
    
    """
    off_bbbb
    """
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def off_bbbb(self):
        
        # 하락세 감지, 모니터링 돌입
        if self.is_bbbb():
            self.pre_on_bbbb(f"{self.pref_msg} {self.cycle_state} 하단 무너짐이 감시 되었습니다. BBBB 모니터링을 시작합니다.")
            return
            
        # CASE 2: 매수 없이 상승세 감지      
        elif self.is_bbbt() and\
            self.is_time_over():
            self.init_cycle(f"{self.pref_msg} {self.cycle_state} 상승세를 감지하였으며 {self.order_reset_hours_if_stable}시간 동안 거래를 감지하지 못하였습니다. 매매롤 초기화 합니다.")
            return
        
    """
    on_bbbb
    """
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_on_bbbb(self, msg=None):
            
        # bbbb의 가격을 현재가로 잡고 bbbb 상태 변경
        self.redis.hupd_date(self.pref_bbbb_price, self.ticker, self.current_price) 
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "on_bbbb")
        
        if msg:
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}")
        
        self.save_cycle_state_changes("on_bbbb")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def on_bbbb(self):
        
        # CASE 1: 매수 포인트 감지   
        if self.is_shooting(): 
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
                self.init_cycle(f"{self.pref_msg} {self.cycle_state} 매수하기 위한 한화가 없습니다. 초기화합니다.")

            # CASE 1-2 : 매수시도액보다 한화량 낮음. 초기화
            elif self.order_seed < self.order_amount:
                self.init_cycle(f"{self.pref_msg} {self.cycle_state} 매수하기 위한 한화가 부족합니다. 초기화합니다.")
            
            # CASE 1-3 : 정상 케이스, 매수
            else:
                self.do_buy_with_up_order_intense()
                self.pre_after_bbbb_mornitoring_pivot_high(f"{self.pref_msg} {self.cycle_state} pivot high 관측을 시작합니다.")
                return
    
        # CASE 2: 매수 없이 상승세 감지, recover      
        elif self.is_bbbt() and\
            self.is_bbbb_recover():
            self.init_state(f"{self.pref_msg} {self.cycle_state} 상승세를 감지하였습니다. BBBB 모니터링을 중단합니다.")
            return
        
        # CASE 3: 매수 없이 상승세 감지, time over      
        elif self.is_bbbt() and\
            self.is_time_over():
            self.init_cycle(f"{self.pref_msg} {self.cycle_state} 상승세를 감지하였으며 {self.order_reset_hours_if_stable}시간 동안 거래를 감지하지 못하였습니다. 매매롤 초기화 합니다.")
            return
              
    """
    after_bbbb
    mornitoring_pivot_high
    """    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_mornitoring_pivot_high(self, msg=None):

        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb")
        self.redis.hupd_date(self.pref_after_bbbb_state, self.ticker, "mornitoring_pivot_high")

        if msg:
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}")
            
        self.save_cycle_state_changes("after_bbbb", "mornitoring_pivot_high")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_mornitoring_pivot_high(self):

        try:
            if self.is_bbbb_out() == True:
                if self.is_lift_up() == True:
                    self.pre_after_bbbb_mornitoring_pivot_low(f"{self.pref_msg} {self.cycle_state} 상승형으로 피벗 전환하였습니다. pivot low 관측을 진행합니다")
                    return
            
            elif self.is_bbbb() == True:
                self.pre_on_bbbb(f"{self.pref_msg} {self.cycle_state} BBBB에 재진입 합니다. BBBB 모니터링을 시작합니다.")
                return
        
        finally:
            self.update_lowest_price()

    """
    after_bbbb
    mornitoring_pivot_low
    """ 
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_mornitoring_pivot_low(self, msg=None):

        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb")
        self.redis.hupd_date(self.pref_after_bbbb_state, self.ticker, "mornitoring_pivot_low")

        if msg : 
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}") 
            
        self.save_cycle_state_changes("after_bbbb", "mornitoring_pivot_low")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_mornitoring_pivot_low(self):

        try:
            if self.is_bbbb() == True:
                self.do_sell()
                self.pre_on_bbbb(f"{self.pref_msg} {self.cycle_state} BBBB에 재진입 하였습니다. BBBB 모니터링을 시작합니다.")
                return
            
            elif self.is_lowest() == True:
                self.do_sell()
                self.pre_after_bbbb_mornitoring_pivot_high(f"{self.pref_msg} {self.cycle_state} 최저가 밑으로 진입하였습니다. pivot high 관측을 시작합니다.")
                return
            
            else:
                if self.is_lift_down() == True:
                    self.pre_after_bbbb_mornitoring_stable(f"{self.pref_msg} {self.cycle_state} 하락형으로 피벗 전환하였습니다. stable 관측을 진행합니다.")
                    return
        finally:
            self.update_lowest_price()

    """
    after_bbbb
    mornitoring_stable
    """ 
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_mornitoring_stable(self, msg=None):

        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb")
        self.redis.hupd_date(self.pref_after_bbbb_state, self.ticker, "mornitoring_stable")
        
        if msg : 
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}") 
            
        self.save_cycle_state_changes("after_bbbb", "mornitoring_stable")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_mornitoring_stable(self):
        
        if self.is_bbbb() == True:
            self.do_sell()
            self.pre_on_bbbb(f"{self.pref_msg} {self.cycle_state} BBBB에 재진입 하였습니다. BBBB 모니터링을 시작합니다.")
            return
            
        else:
            if self.is_lift_up(p=2) == True:
                if self.is_lowest() == True: 
                    self.do_sell()
                    self.pre_after_bbbb_mornitoring_pivot_high(f"{self.pref_msg} {self.cycle_state} 하락형 산구도가 형성되었습니다. pivot high 관측을 시작합니다.")
                    return

                else:
                    self.pre_stable_bbbb(f"{self.pref_msg} {self.cycle_state} 상승형 산구도가 형성되었습니다. BBBB 안정화 단계 모니터링을 시작합니다.")
                    
                    ticks = get_5m_ticks_exact(self.order_last_dt)
                    diff = self.current_price - self.lowest_price
                    diff_rate = (self.current_price - self.lowest_price)/self.lowest_price*100 
                    
                    self.redis.save_msg_on_Q(f"TEST !! : ticks : {ticks}") 
                    self.redis.save_msg_on_Q(f"TEST !! : diff : {diff}") 
                    self.redis.save_msg_on_Q(f"TEST !! : diff_rate : {diff_rate}") 
                    self.redis.save_msg_on_Q(f"TEST !! : self.order_book_date : {self.order_book_date}") 
                    # 상황에 따른 추매
                    # order_control = 
                    # self.do_buy(order_control=0.5)
                        
                    return
    
    """
    stable_bbbb
    """      
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_stable_bbbb(self, msg=None):
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "stable_bbbb")
        self.redis.hupd_date(self.pref_after_bbbb_state, self.ticker, "")

        if msg:
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}") 
        
        # TODO 지정가 초기화 하고 평단에 매수액 절반만큼 매도 걸기
            
        self.save_cycle_state_changes("stable_bbbb")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def stable_bbbb(self):
        
        try:
            if self.is_lowest() == True:
                self.do_sell()
                self.pre_on_bbbb(f"{self.pref_msg} {self.cycle_state} 최저가 밑으로 진입하였습니다. BBBB 모니터링을 시작합니다.")
                return
            
            # TODO : 상승 반전신호 캐치 (임시 로직)
            if self.is_stable_bbbb_recover():

                self.do_buy(up_order_intense=False)
                self.init_cycle(f"{self.slack_post_prefix} : {self.ticker} 상승 반전신호를 캐치하였습니다. 이후 상황을 주시하세요. 사이클을 마무리합니다.")

        finally:
            self.update_lowest_price()
        
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def init_state(self, msg=None):
        
        # 상태만 초기화
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_cycle_state, self.ticker)
        self.redis.hdel_data(self.pref_after_bbbb_state, self.ticker)
        self.redis.hdel_data(self.pref_lowest_price, self.ticker)

        if msg:
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}") 
        
        self.save_cycle_state_changes("init_state")
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def init_cycle(self, msg=None):
        
        # 사이클 전체 초기화
        self.redis.hdel_data(self.pref_cycle_state, self.ticker)
        self.redis.hdel_data(self.pref_after_bbbb_state, self.ticker)
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_lowest_price, self.ticker)
        
        self.redis.hdel_data(self.pref_order_amount, self.ticker)
        self.redis.hdel_data(self.pref_order_hurdle, self.ticker)
        self.redis.hdel_data(self.pref_order_last_dt, self.ticker)

        if msg:
            self.redis.save_msg_on_Q(f"{msg} {self.order_book_date}") 
        
        self.save_cycle_state_changes("init_cycle")
    
    
    """
    transactions
    """
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def do_buy(self, order_control=1):
        
        # 매매 진행
        self.order_last_dt = generate_now_date()
        buy_result = self.upbit.buy_coin(self.order_amount*order_control)
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
            
            self.redis.hupd_date(self.pref_order_last_price, self.ticker, str(self.current_price)) 
            self.redis.hupd_date(self.pref_order_last_dt, self.ticker, str(self.order_last_dt)) 

            # 메세지 포스트
            self.redis.save_msg_on_Q(f"{self.pref_msg} {self.cycle_state} 매수 성공.\n 주문가 : {round(float(buy_result['price']), 2)}, 수수료 : {round(float(buy_result['reserved_fee']))}\n\n")

        else:
            self.init_state("매수에 실패햐였습니다.")
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def do_buy_with_up_order_intense(self):
        
        # 매매 진행
        self.order_last_dt = generate_now_date()
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
            self.redis.save_msg_on_Q(f"{self.pref_msg} {self.cycle_state} 매수 성공.\n 주문가 : {round(float(buy_result['price']), 2)}, 수수료 : {round(float(buy_result['reserved_fee']))}\n\n")
            
            if self.redis.hget_data(self.pref_bbbb_price, self.ticker):         
                self.redis.hupd_date(self.pref_order_amount, self.ticker, (self.order_amount * self.order_percent_ir)) 
                self.redis.hupd_date(self.pref_order_hurdle, self.ticker, (self.order_hurdle * self.order_hurdle_ir))  
                self.redis.hupd_date(self.pref_order_last_price, self.ticker, str(self.current_price)) 
                self.redis.hupd_date(self.pref_order_last_dt, self.ticker, str(self.order_last_dt)) 
        
        else:
            self.init_state("매수에 실패햐였습니다.")
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def do_sell(self):
        
        # 매도 진행
        self.order_last_dt = str(generate_now_date())
        sell_result = self.upbit.sell_coin(self.order_amount/2)
        if sell_result:
            self.log.info(f"sell_result : {sell_result}")
            # params = {
            #     "exchange": "upbit",
            #     "ticker": self.ticker,
            #     "uuid": buy_result.get("uuid"),
            #     "ord_side": buy_result.get("side"),
            #     "ord_type": buy_result.get("ord_type"),
            #     "price": buy_result.get("price"),
            #     "reserved_fee": buy_result.get("reserved_fee"),
            #     "remaining_fee": buy_result.get("remaining_fee"),
            #     "paid_fee": buy_result.get("paid_fee"),
            #     "state": buy_result.get("state"),
            #     "locked": buy_result.get("locked"),
            #     "executed_volume": buy_result.get("executed_volume"),
            #     "runnable_service_seq": self.seq
            # }
            # self.trade_result_dao.insert(params)

            # # 메세지 포스트
            # self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker}의 매수를 성공하였습니다.\n 주문가 : {round(float(buy_result['price']), 2)}, 수수료 : {round(float(buy_result['reserved_fee']))}\n\n")

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def do_sell_with_down_order_intense(self):
        
        # 매도 진행
        self.order_last_dt = generate_now_date()
        sell_result = self.upbit.sell_coin(self.order_amount/2)
        if sell_result:
            self.log.info(f"sell_result : {sell_result}")
            # params = {
            #     "exchange": "upbit",
            #     "ticker": self.ticker,
            #     "uuid": buy_result.get("uuid"),
            #     "ord_side": buy_result.get("side"),
            #     "ord_type": buy_result.get("ord_type"),
            #     "price": buy_result.get("price"),
            #     "reserved_fee": buy_result.get("reserved_fee"),
            #     "remaining_fee": buy_result.get("remaining_fee"),
            #     "paid_fee": buy_result.get("paid_fee"),
            #     "state": buy_result.get("state"),
            #     "locked": buy_result.get("locked"),
            #     "executed_volume": buy_result.get("executed_volume"),
            #     "runnable_service_seq": self.seq
            # }
            # self.trade_result_dao.insert(params)

            # # 메세지 포스트
            # self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker}의 매수를 성공하였습니다.\n 주문가 : {round(float(buy_result['price']), 2)}, 수수료 : {round(float(buy_result['reserved_fee']))}\n\n")

            if self.redis.hget_data(self.pref_bbbb_price, self.ticker):   
                
                # TODO : DEBUG, DELETE 
                self.set_state_bucket()
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_amount : {self.order_amount}") 
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_hurdle : {self.order_hurdle}") 
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_last_dt : {self.order_last_dt}") 
                      
                # TODO : KEEP HERE !! 
                self.redis.hupd_date(self.pref_order_amount, self.ticker, (self.order_amount / self.order_percent_ir)) 
                self.redis.hupd_date(self.pref_order_hurdle, self.ticker, (self.order_hurdle / self.order_hurdle_ir)) 
                self.redis.hupd_date(self.pref_order_last_price, self.ticker, str(self.current_price)) 
                self.redis.hupd_date(self.pref_order_last_dt, self.ticker, str(self.order_last_dt)) 
                
                # TODO : DEBUG, DELETE 
                self.set_state_bucket()
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_amount : {self.order_amount}") 
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_hurdle : {self.order_hurdle}") 
                self.redis.save_msg_on_Q(f"TEST !!! : self.order_last_dt : {self.order_last_dt}") 
                

    """
    Helper
    """
    # Option, Users
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def set_order_option(self):
        
        self.order_percent_iv = self.order_intensity["order_percent_iv"]
        self.order_percent_ir = self.order_intensity["order_percent_ir"]
        self.order_hurdle_iv = self.order_intensity["order_hurdle_iv"]
        self.order_hurdle_ir = self.order_intensity["order_hurdle_ir"]
        self.order_reset_hours_if_stable = self.order_intensity.get("order_reset_hours_if_stable")

        if self.order_percent_iv: self.order_percent_iv = float(self.order_percent_iv)
        else: raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_percent_iv")

        if self.order_percent_ir: self.order_percent_ir = float(self.order_percent_ir) 
        else: raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_percent_ir")

        if self.order_hurdle_iv: self.order_hurdle_iv = float(self.order_hurdle_iv)
        else: raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_hurdle_iv") 

        if self.order_hurdle_ir: self.order_hurdle_ir = float(self.order_hurdle_ir)
        else: raise ValueError(f"class : {self.__class__.__name__}, error : Missing options required: self.order_hurdle_ir")

        if self.order_reset_hours_if_stable: self.order_reset_hours_if_stable = float(self.order_reset_hours_if_stable)
        else: self.order_reset_hours_if_stable = 24
           
    # Standard, Redis
    def set_state_bucket(self):
        
        # state
        self.cycle_state = self.redis.hget_data(self.pref_cycle_state, self.ticker) 
        self.after_bbbb_state = self.redis.hget_data(self.pref_after_bbbb_state, self.ticker) 
        
        # bbbb
        self.bbbb_price = self.redis.hget_data(self.pref_bbbb_price, self.ticker) 
        if self.bbbb_price: 
            self.bbbb_price = float(self.bbbb_price)
        
        self.lowest_price = self.redis.hget_data(self.pref_lowest_price, self.ticker)
        if self.lowest_price: 
            self.lowest_price = float(self.lowest_price)
        
        # order 
        self.order_hurdle = self.redis.hget_data(self.pref_order_hurdle, self.ticker) # 주문 허들
        self.order_amount = self.redis.hget_data(self.pref_order_amount, self.ticker) # 주문량
        
        if self.order_hurdle: self.order_hurdle = float(self.order_hurdle)
        else: self.order_hurdle = self.order_hurdle_iv

        if self.order_amount: self.order_amount = float(self.order_amount)
        else: self.order_amount = 0
        
        self.order_last_price = self.redis.hget_data(self.pref_order_last_price, self.ticker) # 마지막 주문 시간
        if self.order_last_price: self.order_last_price = float(self.order_last_price)
        else: self.order_last_price = 0
        
        self.order_last_dt = self.redis.hget_data(self.pref_order_last_dt, self.ticker) # 마지막 주문 시간
        if self.order_last_dt: self.order_last_dt = datetime.datetime.strptime(self.order_last_dt, "%Y-%m-%d %H:%M:%S")
        else: self.order_last_dt = datetime.datetime.now()
         
    # Indicators, API & Calucator
    def set_indicators(self):
        self.upbit.set_ohlcv(interval="minute5", date=self.order_book_date, count=200)
        self.upbit.set_bollinger_partition()
        self.df = self.upbit.get_df()
        
        self.current_price = self.order_book.get("trade_price") 
        if self.current_price: self.current_price = float(self.current_price)
        else: self.current_price = float(self.df["close"].iloc[-1])
            
        self.close_price_list = [float(c) for c in self.df["close"].iloc[-10:].tolist()]
        self.bollinger_state_crr = int(self.df["bollinger_partition"].iloc[-1])
        self.bollinger_state_prev = int(self.df["bollinger_partition"].iloc[-2])
    
    def update_lowest_price(self):
        
        if self.lowest_price == None:
            self.lowest_price = self.current_price
            self.redis.hupd_date(self.pref_lowest_price, self.ticker, self.lowest_price)
        
        elif self.lowest_price > self.current_price:
            self.lowest_price = self.current_price
            self.redis.hupd_date(self.pref_lowest_price, self.ticker, self.lowest_price)
            
    # Judges
    def is_time_over(self):
        """
        - 지정한 시간동안 거래 없음
        """
        if self.order_reset_hours_if_stable and self.order_last_dt:
            if datetime.timedelta(hours=self.order_reset_hours_if_stable) < (datetime.datetime.now()- self.order_last_dt):
                return True

        return False
        
    def is_bbbb(self):
        """
        - 현재 볼린저 상태가 1
        - 이전 볼린저 상태가 1
        """
        if self.bollinger_state_crr and self.bollinger_state_prev:
            if (self.bollinger_state_crr == 1 and\
                self.bollinger_state_prev == 1):
                    return True

        return False

    def is_bbbb_recover(self):
        
        if self.bbbb_price and self.current_price:
            if (self.bbbb_price * 0.8) < self.current_price:
                return True
        
        return False
    
    def is_bbbb_out(self):
        """
        - 현재 볼린저 상태가 2 상회
        - 이전 볼린저 상태가 1 상회
        """
        if self.bollinger_state_crr and self.bollinger_state_prev:
            if (self.bollinger_state_crr > 2 and\
                self.bollinger_state_prev > 1):
                    return True

        return False
    
    def is_bbbt(self):
        """
        - 현재 볼린저 상태가 6 
        - 이전 볼린저 상태가 5,6
        """
        if self.bollinger_state_crr and self.bollinger_state_prev:
            if (self.bollinger_state_crr in ([6]) and\
                self.bollinger_state_prev in ([5, 6])):
                    return True

        return False
    
    def is_stable_bbbb_recover(self):
        
        if self.order_last_price and self.current_price:
            if (self.order_last_price*1.25) < self.current_price:
                return True
        
        return False
        
    
    def is_lift_up(self, p=3):
        """
        - 2전 종가 < 1전 종가 < 현재가
        """
        if self.close_price_list:
            if len(self.close_price_list) > 3:
                
                c0 = self.current_price
                c1 = self.close_price_list[-1]
                c2 = self.close_price_list[-2]
                c3 = self.close_price_list[-3]
                c4 = self.close_price_list[-4]
                
                s = 0
                if c0 > c1: s += 1
                if c1 > c2: s += 1
                if c2 > c3: s += 1
                if c3 > c4: s += 1
                    
                if s >= p:
                    return True
                    
        return False

    def is_lift_down(self, p=3):
        """
        - 2전 종가 > 1전 종가 > 현재가
        """
        if self.close_price_list:
            if len(self.close_price_list) > 3:
                
                c0 = self.current_price
                c1 = self.close_price_list[-1]
                c2 = self.close_price_list[-2]
                c3 = self.close_price_list[-3]
                c4 = self.close_price_list[-4]
                
                s = 0
                if c0 < c1: s += 1
                if c1 < c2: s += 1
                if c2 < c3: s += 1
                if c3 < c4: s += 1
                    
                if s >= p:
                    return True

        return False
    
    def is_lowest(self):

        if self.lowest_price and self.current_price:
            if self.lowest_price >= self.current_price:
                return True
        
        return False
    
    def is_shooting(self):
        """
        - 현재 볼린저 상태가 1 상회
        - 이전 볼린저 상태가 1 상회
        - 2봉 전 종가보다 전봉 종가가 커야함
        - bbbb당시 가격과 현재가의 변화율이 order_hurdle 이하여야함
        """
        if self.bollinger_state_crr and self.bollinger_state_prev:
            if (self.bollinger_state_crr > 1 and\
                self.bollinger_state_prev > 1 and\
                self.close_price_list[-2] > self.close_price_list[-3] and\
                self.upbit.get_price_diff_rate(self.current_price, self.bbbb_price) > self.order_hurdle):
                return True

        return False
    
    def save_cycle_state_changes(self, cycle_step, after_bbbb_state=None):
        
        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "CvAutoTradeProd02Gen02Core-cycle_state"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "cycle_state"]
        params["result_markerable"] = f"{cycle_step}.{after_bbbb_state}"
        params["result_json"] = None
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["reg_dt"] = self.order_book_date
        params["mod_member_seq"] = 0
        params["mod_dt"] = self.order_book_date

        self.research_result_dao.insert_with_limit(params, 100000)
        
    
    
    # def is_lift_up(self):
    #     """
    #     - 2전 종가 < 1전 종가 < 현재가
    #     """
    #     if self.close_price_list:
    #         if len(self.close_price_list) > 3:
    #             c1 = self.close_price_list[-3]
    #             c2 = self.close_price_list[-2]
    #             c3 = self.current_price
    #             if c1 < c2:
    #                 if c2 < c3:
    #                     return True

    #     return False

    # def is_lift_down(self):
    #     """
    #     - 2전 종가 > 1전 종가 > 현재가
    #     """
    #     if self.close_price_list:
    #         if len(self.close_price_list) > 3:
    #             c1 = self.close_price_list[-3]
    #             c2 = self.close_price_list[-2]
    #             c3 = self.current_price

    #             if c1 > c2:
    #                 if c2 > c3:
    #                     return True

    #     return False
    
    # def is_pivot_lil_high(self):
    #     if self.close_price_list:
    #         if len(self.close_price_list) > 3:
    #             c2 = self.close_price_list[-2]
    #             c3 = self.current_price
    #             if c2 < c3:
    #                 return True

    #     return False
    
    