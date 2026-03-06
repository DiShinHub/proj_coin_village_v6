from background.modules.log import system_module_log
from background.dao.runnable_services_dao import runnableServicesDao

from apscheduler.schedulers.blocking import BlockingScheduler
import time

class ServiceHandler():
    
    def __init__(
            self, 
            seq=None, 
            interval_options=None, 
            schedule_options=None, 
            **kwargs
        ):
        self.log = system_module_log
        self.runnable_service_dao = runnableServicesDao()

        self.seq = seq
        self.interval_options = interval_options
        self.schedule_options = schedule_options

        self.interval_term = None
        if interval_options:
            if interval_options.get("interval_term"):
                self.interval_term = interval_options.get("interval_term")

        self.start_day = None
        self.start_hour = None
        self.start_min = None
        if schedule_options:
            if schedule_options.get("start_day"):
                self.start_day = schedule_options.get("start_day")
            if schedule_options.get("start_hour"):
                self.start_hour = schedule_options.get("start_hour")
            if schedule_options.get("start_min"):
                self.start_min = schedule_options.get("start_min")

    def run(self):
        
        # 실행
        res = self.main()
            
        # 스스로를 종료
        self.runnable_service_dao.update_runnable_services(
            params={
                "activate_yn" : "N"
            },
            seq=self.seq
        )
        return res
    
    def socket(self):
        res = self.main()
        return res

    def schedule(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(
            self.main, 
            'cron', 
            day=self.start_day, 
            hour=self.start_hour, 
            minute=self.start_min,
            second=0,
            max_instances=1,
            coalesce=True
        )
        scheduler.start()
    
    def interval(self):

        while True:
            self.main()
            if self.interval_term:
                time.sleep(self.interval_term)
    
    def main(self):
        # override here 
        pass