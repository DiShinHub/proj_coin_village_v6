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
        
        # --- 모드 설정
        self.cycle_state = None                      # 모드
        
        # --- 유동 값
        self.current_price = None             # 현재가
        self.close_price_list = []            # 종가 리스트
        self.bbbb_price = None                # bbbb가격
        self.bollinger_state_prev = None      # 이전 볼린저 상태 값
        self.bollinger_state_crr = None       # 현재 볼린저 상태 값
        self.order_seed = 0                   # 주문 시드
        self.order_amount = 0                 # 주문 비중
        self.order_hurdle = 0                 # 주문 허들
        self.order_last_dt = None             # 마지막 주문 시간

        self.pivot_state = None
        
        # --- prefixes
        self.pref_servce = str(self.__class__.__name__)
        self.pref_cycle_state = f"{self.pref_servce}_{self.ticker}_cycle_state"          # 사이클 상태
        
        self.pref_bbbb_price = f"{self.pref_servce}_{self.ticker}_bbbb_price"            # bbbb 가격 
        self.pref_order_amount = f"{self.pref_servce}_{self.ticker}_order_amount"        # 주문량 
        self.pref_order_hurdle = f"{self.pref_servce}_{self.ticker}_order_hurdle"        # 주문 허들 
        self.pref_order_last_dt = f"{self.pref_servce}_{self.ticker}_order_last_dt"      # 마지막 주문 시간
        self.pref_lowest_price_after_bbbb = f"{self.pref_servce}_{self.ticker}_lowest_price_after_bbbb"
        
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
                
            elif self.cycle_state == "on_bbbb_out":
                self.on_bbbb_out()
                
            elif self.cycle_state == "after_bbbb_unstable_pivot_high":
                self.after_bbbb_unstable_pivot_high()
                
            elif self.cycle_state == "after_bbbb_unstable_pivot_low":
                self.after_bbbb_unstable_pivot_low()
                
            else:
                self.off_bbbb()
        
        except Exception as e:
            self.log.info(f"{str(e)}")
    
    """
    Cycle
    """
    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def off_bbbb(self):
        self.set_indicators()
        
        # 하락세 감지, 모니터링 돌입
        if self.is_bbbb():
            self.pre_on_bbbb()
            return
            
        # CASE 2: 매수 없이 상승세 감지      
        elif self.is_bbbt() and\
            self.is_time_over():
            self.init_cycle(f"{self.slack_post_prefix} : {self.ticker}의 상승세를 감지하였으며 {self.order_reset_hours_if_stable}시간 동안 거래를 감지하지 못하였습니다. 매매롤 초기화 합니다.")

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_on_bbbb(self, msg=None):
        
        if msg:
            self.redis.save_msg_on_Q(msg)
            
        # bbbb의 가격을 현재가로 잡고 bbbb 상태 변경
        self.redis.hupd_date(self.pref_bbbb_price, self.ticker, self.current_price) 
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "on_bbbb")
        self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker}의 하단 무너짐이 감시 되었습니다. 모니터링을 시작합니다.")

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
                self.init_cycle(f"{self.slack_post_prefix} : {self.ticker}를 매수하기 위한 한화가 없습니다. 초기화합니다.")

            # CASE 1-2 : 매수시도액보다 한화량 낮음. 초기화
            elif self.order_seed < self.order_amount:
                self.init_cycle(f"{self.slack_post_prefix} : {self.ticker}을 매수하기 위한 한화가 부족합니다. 초기화합니다.")
            
            # CASE 1-3 : 정상 케이스, 매수
            else:
                self.pre_on_bbbb_out()
                return
    
        # CASE 2: 매수 없이 상승세 감지      
        elif self.bollinger_state_crr in ([6]) and\
            self.bollinger_state_prev in ([5, 6]):
            self.init_state(f"{self.slack_post_prefix} : {self.ticker}의 상승세를 감지하였습니다. 모니터링을 중단합니다.")

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_on_bbbb_out(self):

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
            bbbb_price_here = self.redis.hget_data(self.pref_bbbb_price, self.ticker)
            self.log.info(f"bbbb_price_here1 : {bbbb_price_here}")

            if self.redis.hget_data(self.pref_bbbb_price, self.ticker):         
                self.log.info(f"bbbb_price_here2 : {bbbb_price_here}")   
                self.log.info(f"self.order_amount : {self.order_amount}")   
                self.log.info(f"self.order_percent_ir : {self.order_percent_ir}")
                self.log.info(f"self.order_hurdle : {self.order_hurdle}")   
                self.log.info(f"self.order_hurdle_ir : {self.order_hurdle_ir}")
                self.redis.hupd_date(self.pref_order_amount, self.ticker, (self.order_amount * self.order_percent_ir)) 
                self.redis.hupd_date(self.pref_order_hurdle, self.ticker, (self.order_hurdle * self.order_hurdle_ir))  
                self.redis.hupd_date(self.pref_order_last_dt, self.ticker, order_dt) 
        
            # 상태 변경
            self.redis.hupd_date(self.pref_cycle_state, self.ticker, "on_bbbb_out")
        
        else:
            self.init_state("매수에 실패햐였습니다.")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def on_bbbb_out(self):

        if self.is_bbbb_out() == True:
            if self.is_lift_up() == True:
                self.pre_after_bbbb_unstable_pivot_high()
                return

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_unstable_pivot_high(self):
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb_unstable_pivot_high")
        self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker} 상승형 피벗 전환입니다.")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_unstable_pivot_high(self):
        
        if self.lowest_price_after_bbbb == None:
            self.lowest_price_after_bbbb = self.current_price
            self.redis.hupd_date(self.pref_lowest_price_after_bbbb, self.ticker, self.lowest_price_after_bbbb)
        
        elif self.lowest_price_after_bbbb > self.current_price:
            self.lowest_price_after_bbbb = self.current_price
            self.redis.hupd_date(self.pref_lowest_price_after_bbbb, self.ticker, self.lowest_price_after_bbbb)

        if self.is_bbbb() == True:
            self.pre_on_bbbb(f"{self.slack_post_prefix} : {self.ticker} BBBB에 재진입 합니다.")
        
        else:
            if self.is_lift_down() == True:
                self.pre_after_bbbb_unstable_pivot_low()

    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_unstable_pivot_low(self):
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb_unstable_pivot_low")
        self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker} 하락형 피벗 전환입니다.")

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_unstable_pivot_low(self):

        if self.is_bbbb() == True:
            self.pre_on_bbbb(f"{self.slack_post_prefix} : {self.ticker} BBBB에 재진입 합니다.")
        
        else:
            if self.is_lift_up() == True:
                if self.lowest_price_after_bbbb > self.current_price:
                    self.init_state(f"{self.slack_post_prefix} : {self.ticker} 하락형 산구도가 형성되었습니다.")

                else:
                    self.pre_after_bbbb_stable()
                    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1) 
    def pre_after_bbbb_stable(self):
        
        self.redis.hupd_date(self.pref_cycle_state, self.ticker, "after_bbbb_stable")
        self.redis.save_msg_on_Q(f"{self.slack_post_prefix} : {self.ticker} 상승형 산구도가 형성되었습니다. bbbb 안정화 단계 모니터링에 돌입합니다.") 
        
        # 아마 추매
        # 그리고 지정가 지정하여 평단에서 50% 정도 팔기
        """
        TEST START
        """
        self.upbit.set_rsi()
        self.upbit.set_atr()
        self.upbit.set_atr_ratio()
        self.upbit.set_bollinger_width()
        self.upbit.set_obv()
        self.upbit.set_vwap()
        self.upbit.set_volume_volatility()
        self.upbit.set_volume_spike()
        self.df = self.upbit.get_df()
        
        self.rsi_list = [float(c) for c in self.df["rsi"].iloc[-10:].tolist()] 
        self.atr_list = [float(c) for c in self.df["atr"].iloc[-10:].tolist()] 
        self.atr_ratio_list = [float(c) for c in self.df["atr_ratio"].iloc[-10:].tolist()] 
        self.bollinger_width_list = [float(c) for c in self.df["bollinger_width"].iloc[-10:].tolist()] 
        self.obv_list = [float(c) for c in self.df["obv"].iloc[-10:].tolist()] 
        self.volume_volatility_list = [float(c) for c in self.df["vwvolume_volatilityap"].iloc[-10:].tolist()] 
        self.volume_spike_list = [float(c) for c in self.df["volume_spike"].iloc[-10:].tolist()] 
        
        data_list = self.research_result_dao.gets(
            page_no=1,
            row_count=10,
            type="upbit-regime", 
            ticker=self.ticker
        )
        self.upbit_regime_list = data_list[0:10]
        
        data_list = self.research_result_dao.gets(
            page_no=1,
            row_count=10,
            type="upbit-direction", 
            ticker=self.ticker
        )
        self.upbit_direction_list = data_list[0:10]
        
        self.log.info(f"=================== pre_after_bbbb_stable ========================")
        self.log.info(f"self.rsi_list : {self.rsi_list}")
        self.log.info(f"self.atr_list : {self.atr_list}")
        self.log.info(f"self.atr_ratio_list : {self.atr_ratio_list}")
        self.log.info(f"self.bollinger_width_list : {self.bollinger_width_list}")
        self.log.info(f"self.obv_list : {self.obv_list}")
        self.log.info(f"self.volume_volatility_list : {self.volume_volatility_list}")
        self.log.info(f"self.volume_spike_list : {self.volume_spike_list}")
        self.log.info(f"self.upbit_regime_list : {self.upbit_regime_list}")
        self.log.info(f"self.upbit_direction_list : {self.upbit_direction_list}")
        self.log.info(f"=================== pre_after_bbbb_stable ========================")
        
        """
        TEST END
        """

    @block_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def after_bbbb_stable(self):
        
        if self.lowest_price_after_bbbb > self.current_price:
            self.init_state(f"{self.slack_post_prefix} : {self.ticker} 최하단 돌파입니다. 상태를 초기화힙니다.")
        
        if self.is_bbbb():
            self.pre_on_bbbb(f"{self.slack_post_prefix} : {self.ticker} BBBB에 재진입 합니다.")
        
        # TODO 이건 지워야함 나중에, 테스팅 제약 용도
        if self.is_bbbt():
            self.init_state(f"{self.slack_post_prefix} : {self.ticker} 상승캐치, 테스팅 종료")
            
        """
        TEST START
        """
        self.upbit.set_rsi()
        self.upbit.set_atr()
        self.upbit.set_atr_ratio()
        self.upbit.set_bollinger_width()
        self.upbit.set_obv()
        self.upbit.set_vwap()
        self.upbit.set_volume_volatility()
        self.upbit.set_volume_spike()
        self.df = self.upbit.get_df()
        
        self.rsi_list = [float(c) for c in self.df["rsi"].iloc[-10:].tolist()] 
        self.atr_list = [float(c) for c in self.df["atr"].iloc[-10:].tolist()] 
        self.atr_ratio_list = [float(c) for c in self.df["atr_ratio"].iloc[-10:].tolist()] 
        self.bollinger_width_list = [float(c) for c in self.df["bollinger_width"].iloc[-10:].tolist()] 
        self.obv_list = [float(c) for c in self.df["obv"].iloc[-10:].tolist()] 
        self.volume_volatility_list = [float(c) for c in self.df["vwvolume_volatilityap"].iloc[-10:].tolist()] 
        self.volume_spike_list = [float(c) for c in self.df["volume_spike"].iloc[-10:].tolist()] 
        
        data_list = self.research_result_dao.gets(
            page_no=1,
            row_count=10,
            type="upbit-regime", 
            ticker=self.ticker
        )
        self.upbit_regime_list = data_list[0:10]
        
        data_list = self.research_result_dao.gets(
            page_no=1,
            row_count=10,
            type="upbit-direction", 
            ticker=self.ticker
        )
        self.upbit_direction_list = data_list[0:10]
        
        self.upbit.set_ichimoku_cloud_state()
        self.df = self.upbit.get_df()
        
        self.bull_cloud_list = [float(c) for c in self.df["bull_cloud"].iloc[-10:].tolist()]
        self.bear_cloud_list = [float(c) for c in self.df["bear_cloud"].iloc[-10:].tolist()]
        
        self.enter_cloud_list = [float(c) for c in self.df["enter_cloud"].iloc[-10:].tolist()]
        self.enter_bull_cloud_list = [float(c) for c in self.df["enter_bull_cloud"].iloc[-10:].tolist()]
        self.enter_bear_cloud_list = [float(c) for c in self.df["enter_bear_cloud"].iloc[-10:].tolist()]
        self.break_up_cloud_list = [float(c) for c in self.df["break_up_cloud"].iloc[-10:].tolist()]
        self.cloud_mid_list = [float(c) for c in self.df["cloud_mid"].iloc[-10:].tolist()]
        self.entry_cloud_slope_list = [float(c) for c in self.df["entry_cloud_slope"].iloc[-10:].tolist()]
        
        # 클라우드 진입전/진입의 상태를 나눠야할 수도 있겠다 
        # 진입 시점의 시간 레디스에 기록
        # 돌파 시점의 시간 레디스에 기록
        # 두 시간의 기울기 = 강도 삼아 추매
        self.log.info(f"=================== after_bbbb_stable ========================")
        self.log.info(f"self.rsi_list : {self.rsi_list}")
        self.log.info(f"self.atr_list : {self.atr_list}")
        self.log.info(f"self.atr_ratio_list : {self.atr_ratio_list}")
        self.log.info(f"self.bollinger_width_list : {self.bollinger_width_list}")
        self.log.info(f"self.obv_list : {self.obv_list}")
        self.log.info(f"self.volume_volatility_list : {self.volume_volatility_list}")
        self.log.info(f"self.volume_spike_list : {self.volume_spike_list}")
        self.log.info(f"self.upbit_regime_list : {self.upbit_regime_list}")
        self.log.info(f"self.upbit_direction_list : {self.upbit_direction_list}")
        
        self.log.info(f"self.bull_cloud_list : {self.bull_cloud_list}")
        self.log.info(f"self.bear_cloud_list : {self.bear_cloud_list}")
        self.log.info(f"self.enter_cloud_list : {self.enter_cloud_list}")
        self.log.info(f"self.enter_bull_cloud_list : {self.enter_bull_cloud_list}")
        self.log.info(f"self.enter_bear_cloud_list : {self.enter_bear_cloud_list}")
        self.log.info(f"self.break_up_cloud_list : {self.break_up_cloud_list}")
        self.log.info(f"self.cloud_mid_list : {self.cloud_mid_list}")
        self.log.info(f"self.entry_cloud_slope_list : {self.entry_cloud_slope_list}")
        self.log.info(f"=================== after_bbbb_stable ========================")
        
        """
        TEST END
        """
        
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def init_state(self, msg):
        
        # 상태만 초기화
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_cycle_state, self.ticker)
        self.redis.hdel_data(self.pref_lowest_price_after_bbbb, self.ticker)
        self.redis.save_msg_on_Q(msg)
    
    @lock_transaction(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY, hold=1)
    def init_cycle(self, msg):
        # 사이클 초기화
        self.redis.hdel_data(self.pref_bbbb_price, self.ticker)
        self.redis.hdel_data(self.pref_cycle_state, self.ticker)
        self.redis.hdel_data(self.pref_lowest_price_after_bbbb, self.ticker)
        
        self.redis.hdel_data(self.pref_order_amount, self.ticker)
        self.redis.hdel_data(self.pref_order_hurdle, self.ticker)
        self.redis.hdel_data(self.pref_order_last_dt, self.ticker)
        self.redis.save_msg_on_Q(msg)
    
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
            
    # Indicators, API & Calucator
    def set_indicators(self):
        self.upbit.set_ohlcv(interval="minute5")
        self.upbit.set_bollinger_partition()
        self.df = self.upbit.get_df()
        
        self.current_price = self.order_book.get("trade_price") 
        if self.current_price: self.current_price = float(self.current_price)
        else: self.current_price = float(self.df["close"].iloc[-1])
            
        self.close_price_list = [float(c) for c in self.df["close"].iloc[-10:].tolist()]
        self.bollinger_state_crr = float(self.df["bollinger_partition"].iloc[-1])
        self.bollinger_state_prev = float(self.df["bollinger_partition"].iloc[-2])
    
    # Standard, Redis
    def set_state_bucket(self):
        
        # state
        self.cycle_state = self.redis.hget_data(self.pref_cycle_state, self.ticker) 
        
        # bbbb
        self.bbbb_price = self.redis.hget_data(self.pref_bbbb_price, self.ticker) 
        if self.bbbb_price: 
            self.bbbb_price = float(self.bbbb_price)
        
        self.lowest_price_after_bbbb = self.redis.hget_data(self.pref_lowest_price_after_bbbb, self.ticker)
        if self.lowest_price_after_bbbb: 
            self.lowest_price_after_bbbb = float(self.lowest_price_after_bbbb)
        
        # order 
        self.order_hurdle = self.redis.hget_data(self.pref_order_hurdle, self.ticker) # 주문 허들
        self.order_amount = self.redis.hget_data(self.pref_order_amount, self.ticker) # 주문량
        
        if self.order_hurdle: self.order_hurdle = float(self.order_hurdle)
        else: self.order_hurdle = self.order_hurdle_iv

        if self.order_amount: self.order_amount = float(self.order_amount)
        else: self.order_amount = 0
        
        self.order_last_dt = self.redis.hget_data(self.pref_order_last_dt, self.ticker) # 마지막 주문 시간
        if self.order_last_dt: self.order_last_dt = datetime.datetime.strptime(self.order_last_dt, "%Y-%m-%d %H:%M:%S")
        else: self.order_last_dt = datetime.datetime.now()
    
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
    
    def is_lift_up(self):
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
                    
                if s >= 3:
                    return True
                    
        return False

    def is_lift_down(self):
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
                    
                if s >= 3:
                    return True

        return False
    
    
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
    
    