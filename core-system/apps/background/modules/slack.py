from background.modules.log import system_module_log
from background.config.config import Config

import inspect

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

class Slack():

    def __init__(self, channel=None):
        self.log = system_module_log
        self.slack_client = Config().set_slack()
        
        self.channel = channel
    
    def set_channel(self, channel):
        self.channel = channel
    
    def post_msg(self, msg):

        try:
            self.slack_client.chat_postMessage(
                channel=self.channel,
                text=msg
            )

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise
    