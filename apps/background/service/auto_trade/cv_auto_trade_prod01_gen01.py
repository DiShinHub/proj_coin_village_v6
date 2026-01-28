from background.middlewares.service_handler import ServiceHandler
from background.constance.upbit_constance import UpbitConst

from background.modules.log import Log
from background.modules.redis import r as redis_single

import websocket
import json
import time
import os

class CvAutoTradeProd01Gen01(ServiceHandler):
    """
    Service Name : CvAutoTradeProd01
    Generation : 01 
    
    Desc : 
    - 호가창 조회
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

        self.socket_url = "wss://api.upbit.com/websocket/v1"
    
    def main(self):

        try:
            ws = websocket.WebSocketApp(self.socket_url,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
            
            ws.on_open = self.on_open
            ws.run_forever()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    """
    socks
    """
    def on_open(self, ws):

        ticker_list = self.service_options.get("ticker_list")
        if not ticker_list:
            self.log.info(f"class : {self.__class__.__name__},  error : no ticker_list found")
            raise Exception("no ticker_list found")
        
        params = [{"ticket": "test"}, {"type": "ticker", "codes": ticker_list}]
        ws.send(json.dumps(params))
        self.log.info(f"WebSocket opened. Subscribed: {ticker_list}")
        return 

    def on_close(self, ws, close_status_code, close_msg):
        self.log.info(f"WebSocket closed, close_status_code : {close_status_code}, close_msg : {close_msg}")
        self.reconnect()
        return 

    def on_error(self, ws, error):
        self.log.info(f"Error:", error)
        self.reconnect()
        return 

    def on_message(self, ws, message):
        data = json.loads(message)
    
        ticker = data.get('code')
        timestamp = time.time()
        key=f"{UpbitConst.ORDERBOOK_QUEUE_KEY}_{ticker}_{timestamp}"
        self.push_to_queue(key, message)
        return data
    
    def reconnect(self):
        
        self.log.info("Reconnecting in 5 seconds...")
        time.sleep(5)
        try:
            self.main()
            
        except Exception as e:
            self.log.error(f"Reconnect failed: {e}")
            time.sleep(10)

    """
    biz
    """
    def push_to_queue(self, key, message):

        self.redis.set_data(
            key=key,
            val=message, 
            expire=self.service_options.get("ttl_orderbook")
        )