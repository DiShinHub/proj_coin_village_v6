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

        self.groups = None
        self.rotate_term = None
        self.set_service_options()
    
    def set_service_options(self):
        res = self.runnable_services_dao.get_CvResearchProd02Gen01_runnable_service()
        self.groups = res["service_options"]["groups"]
        self.rotate_term = res["service_options"]["rotate_term"]

    def main(self):
        self.rotate_group()

    def rotate_group(self):

        index = 0
        threads = []
        drivers = []

        try:
            while True:

                # 그룹 레이아웃 
                target_group = self.groups[index]
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

                # 키보드 입력, 타임 로테이트 대기 
                start_time = time.time()
                while True:

                    if keyboard.is_pressed("space") and keyboard.is_pressed("right"):
                        print(">> 다음 그룹")
                        index = (index + 1) % len(self.groups)
                        break

                    if keyboard.is_pressed("space") and keyboard.is_pressed("left"):
                        print(">> 이전 그룹")
                        index = (index - 1) % len(self.groups)
                        break

                    if time.time() - start_time >= self.rotate_term:
                        index = (index + 1) % len(self.groups)
                        break

                    time.sleep(0.1)

                # 쓰레드, 드라이버 종료
                for t in threads:
                    if t.is_alive():
                        t.join(timeout=5)

                for driver in drivers:
                    driver.quit()
                
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

    def open_url(self, driver, url):
        driver.get(url)

svc = CvResearchProd02Gen01()
svc.main()