from background.modules.log import Log
from background.modules.slack import *
from background.modules.redis import r as redis_single

import time
import os

class CvMessengerGen01():
    """
    Service Name : Slack Messenger
    Generation : 01 
    Product Name : Nan
    
    Desc : 
    - 메세지 큐 확인
    - 메세지가 존재하면 포멧팅 해서 슬랙 전송
    """

    def __init__(self, seq=None, service_options=None):
        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = redis_single
        self.slack = Slack(channel="#coinvillage")
        
        self.pref_slack_msg_box = "slack_msg_box"
    
    def run(self):
        
        while True:
            try:
                data_list = self.get_msg_from_queue()
                if data_list:
                    self.post_msg_from_queue(data_list)
                    
                else:
                    self.log.info("test")
                    time.sleep(1)

            except Exception as e:
                self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
                time.sleep(1)
                    
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
