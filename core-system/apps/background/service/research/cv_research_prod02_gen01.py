from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.eda_dao import EdaDao

from sklearn.ensemble import RandomForestClassifier
import shap

import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
import os

import datetime

class CvResearchProd02Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd02Gen01
    Generation : 01 
    
    Desc : 
    - 폼포코 
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
        
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        self.minio = MinioModule()

        self.eda_dao = EdaDao()

        self.tickers = self.service_options.get("tickers")
        self.ticker = None
    
    def main(self):
        pass