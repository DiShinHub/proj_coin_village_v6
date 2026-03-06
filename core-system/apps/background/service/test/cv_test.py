from background.middlewares.service_handler import ServiceHandler

from background.modules.log import Log
from background.modules.redis import Redis

import os

class CvRedisCleanerGen01(ServiceHandler):
    slack_post_prefix = "tester"

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
        pass