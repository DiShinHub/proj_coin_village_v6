from modules.log import logger
from modules.seleniums import Seleniums
from dao.runnable_services_dao import runnableServicesDao

import keyboard
import threading
import time

class CvResearchProd02Gen01:

    def __init__(self):
        self.log = logger
        self.seleniums = Seleniums()
        self.runnable_services_dao = runnableServicesDao()

        self.change_event = threading.Event()
        self.index = 0
        self.groups = None
        self.rotate_term = None
        self.set_service_options()
    
    def set_service_options(self):
        res = self.runnable_services_dao.get_CvResearchProd02Gen01_runnable_service()
        self.groups = res["service_options"]["groups"]
        self.rotate_term = res["service_options"]["rotate_term"]

    def main(self):
        
        keyboard.add_hotkey("space+right", self.next_group)
        keyboard.add_hotkey("space+left", self.prev_group)
        self.rotate_group()

    def rotate_group(self):

        try:
            while True:
                threads = []
                drivers = []
                start_time = time.time()

                # 그룹 레이아웃 
                target_group = self.groups[self.index]
                screen_width, screen_height = self.seleniums.get_screen_size()
                layout = self.seleniums.get_layout(screen_width, screen_height, target_group["split"])

                # 드라이버 실행
                i = 0
                for url in target_group["urls"]:
                    x, y, w, h = layout[i]
                    
                    driver = self.seleniums.create_driver(x, y, w, h)
                    drivers.append(driver)

                    t = threading.Thread(
                        target=self.open_url,
                        args=(driver, url)
                    )
                    t.daemon = True
                    t.start()
                    threads.append(t)
                    i += 1
                    
                # 다음 이벤트 대기
                self.change_event.clear()
                triggered = self.change_event.wait(timeout=self.rotate_term)
                if not triggered:
                    self.index = (self.index + 1) % len(self.groups)

                # 쓰레드, 드라이버 종료
                for t in threads:
                    if t.is_alive():
                        t.join(timeout=5)

                for driver in drivers:
                    driver.quit()
                
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    def next_group(self):
        print(">> 다음 그룹")
        self.index = (self.index + 1) % len(self.groups)
        self.change_event.set()

    def prev_group(self):
        print(">> 이전 그룹")
        self.index = (self.index - 1) % len(self.groups)
        self.change_event.set()
    
    def open_url(self, driver, url):
        driver.get(url)

svc = CvResearchProd02Gen01()
svc.main()