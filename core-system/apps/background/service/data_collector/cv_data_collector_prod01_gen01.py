from background.middlewares.service_handler import ServiceHandler
from background.constance.upbit_constance import UpbitConst

from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.functions.common_function import *
from background.dao.research_result_dao import ResearchResultDao
from background.decorations.transaction_lock import *

import time
import os

class CvDataCollectorProd01Gen01(ServiceHandler):
    """
    Service Name : CvDataCollectorProd01Gen01
    Generation : 01 
    
    Desc : 
    - 
    """
    pref_slack_msg_box = ""

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        super().__init__(interval_options, schedule_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
    
        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        self.minio = MinioModule()
        self.research_result_dao = ResearchResultDao()
        
        self.tickers = self.service_options["tickers"]
        self.days = self.service_options["days"]
        self.interval_ = self.service_options["interval"]
        
    def main(self):
        """
        
        1. n일치 내 bbbb after stable기간을 추린다 (n일치 == 옵션)
        2. 기간내 df를 뽑아 올린다 
        """
        
        # from option, set days
        self.days = 62
        
        # from db, set target_terms
        # self.research_result_dao.get()...
        
        target_terms = [
            {
                "from" : "",
                "to" : ""
            }
        ]

        try:
            for ticker in self.tickers:
                for term in target_terms:
                    self.generate_df(
                        ticker=ticker, 
                        term=term, 
                        interval=self.interval_
                    )
                    time.sleep(0.25)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    @wait_when_lock(lock_key=UpbitConst.TRANSACTION_BLOCK_KEY)
    def generate_df(self, ticker, term, interval):
        
        self.upbit.set_ticker(ticker)
        
        try:
            # 저장경로 설정
            local_path_5 = self.minio.generate_local_path("csv")
            local_path_15 = self.minio.generate_local_path("csv")
            minio_path_5 = f"eda/stable_bbbb/{ticker}/{term["from"].replace(' ', '')}_{term["to"].replace(' ', '')}_5m.csv"
            minio_path_15 = f"eda/stable_bbbb/{ticker}/{term["from"].replace(' ', '')}_{term["to"].replace(' ', '')}_15m.csv"
            
            # handle for 5m
            self.upbit.set_ohlcvs(interval=interval, count=200, days=30, from_=term["from"], to_=term["to"])
            self.upbit.set_all_features()
            df_5 = self.upbit.get_df()
            df_5.to_csv(local_path_5, index=False)
            
            self.minio.upload_file(
                minio_file_path = minio_path_5, 
                local_file_path = local_path_5, 
                content_type = "text/csv", 
                metadata = {
                    "Content-Disposition": "inline"
                })

            # handle for 15m
            self.upbit.set_df(self.upbit.convert_5m_to_15m(df_5))
            self.upbit.set_all_features()
            
            df_15 = self.upbit.get_df()
            df_15.to_csv(local_path_15, index=False)
    
            self.minio.upload_file(
                minio_file_path = minio_path_15, 
                local_file_path = local_path_15, 
                content_type = "text/csv", 
                metadata = {
                    "Content-Disposition": "inline"
                })
        
        except Exception as e:
            self.log.info(f"{str(e)}")
        
        finally:
            if os.path.exists(local_path_5):
                os.remove(local_path_5)
                
            if os.path.exists(local_path_15):
                os.remove(local_path_15)