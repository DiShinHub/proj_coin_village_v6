from background.middlewares.service_activation_handler import ServiceActivationHandler

from background.modules.log import Log
from background.modules.slack import Slack
from background.modules.redis import r as redis_single

import time
import os

class CvMessengerGen01(ServiceActivationHandler):
    """
    Service Code : CvRedisCleaner
    Generation : 01 
    
    Desc : 
    - 메세지 큐 확인
    - 메세지가 존재하면 포멧팅 해서 슬랙 전송
    """
    pref_slack_msg_box = "slack_msg_box"

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
        self.slack = Slack(channel="#coinvillage")
    
    def main(self):

        try:
            data_list = self.get_msg_from_queue()
            if data_list:
                self.post_msg_from_queue(data_list)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
                    
    def get_msg_from_queue(self):
        
        data_list = self.redis.lrange_all(self.pref_slack_msg_box)
        return data_list
                
    def post_msg_from_queue(self, data_list):

        msg = ""
        for item in reversed(data_list):
            self.redis.lpop(self.pref_slack_msg_box)
            item = item.decode("utf-8")

            if msg:
                msg += f"\n{item}"
            
            else:
                msg = f"{item}" 

        if msg:
            self.slack.post_msg(msg)
