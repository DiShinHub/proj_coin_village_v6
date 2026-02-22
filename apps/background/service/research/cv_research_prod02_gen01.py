from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.eda_dao import EdaDao


import os 
import datetime

class CvResearchProd02Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd02Gen01
    Generation : 01 
    
    Desc : 
    - heatmaps_volume_time_week
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
        self.urls = self.service_options.get("urls")
        self.rotate_term = self.service_options.get("rotate_term")
    
    def main(self):
        pass
