from background.modules.log import Log
from background.modules.slack import *
from background.modules.redis import r as redis_single

import time
import os

class CvTest():

    def __init__(self, seq, service_options=None):
        self.log = Log(os.path.basename(__file__)).get_logger()
        
        self.seq = seq
        self.service_options = service_options
        
    def run(self):
        self.log.info("test")
        self.log.info(f"seq : {self.seq}")
        self.log.info(f"service_options : {self.service_options}")
        return 
        