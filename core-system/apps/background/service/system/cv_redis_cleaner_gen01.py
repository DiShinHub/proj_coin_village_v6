from background.middlewares.service_handler import ServiceHandler

from background.modules.log import Log
from background.modules.redis import Redis

import os

class CvRedisCleanerGen01(ServiceHandler):
    """
    Service Code : CvRedisCleaner
    Generation : 01 
    
    Desc : 
    - 레디스 플러시
    """

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        super().__init__(seq, interval_options, schedule_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = Redis()

    def main(self):

        try:
            self.log.info("레디스를 청소합니다.")
            self.redis.flushall()
            self.log.info("레디스를 청소하였습니다.")

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
