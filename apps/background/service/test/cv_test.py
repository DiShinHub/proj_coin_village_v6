from background.modules.log import Log
from background.modules.slack import *
from background.modules.redis import r as redis_single

from apscheduler.schedulers.blocking import BlockingScheduler

import time
import os

class CvTest():

    def __init__(self, seq, 
            interval_options=None,
            schedule_options=None,
            service_options=None,
        ):
        self.log = Log(os.path.basename(__file__)).get_logger()
        
        self.seq = seq
        self.interval_options = interval_options
        self.schedule_options = schedule_options
        self.service_options = service_options
        
    def interval(self):
        
        while True:
            self.run()
            time.sleep(self.interval_options["interval_term"])
        
    def schedule(self):
        
        redis_single.save_msg_on_Q(f"{self.slack_post_prefix} 스케쥴러 등록. {self.ticker_list}를 대상으로 {self.dataset_load_term}일의 데이터로 학습하며, 매월 {self.scheduler_start_day}일일, {self.scheduler_start_hour}시 {self.scheduler_start_min}분에 실행.")
        scheduler = BlockingScheduler()

        start_day = self.schedule_options.get("start_day")
        start_hour = self.schedule_options.get("start_hour")
        start_min = self.schedule_options.get("start_min")
        scheduler.add_job(self.run, 'cron', day=start_day, hour=start_hour, minute=start_min)
        scheduler.start()
        
    def run(self):
        self.log.info("test")
        self.log.info(f"seq : {self.seq}")
        self.log.info(f"service_options : {self.service_options}")
        