from modules.log import logger
from modules.seleniums import Seleniums

import threading
import time

class RotateUrls:

    def __init__(self):
        self.log = logger
        self.seleniums = Seleniums()

    def main(self):

        self.groups = [
            {
                "split" : "3-top",
                "urls" : [
                    "https://www.binance.com/en/trade/BTC_USDT",
                    "https://www.binance.com/en/trade/ETH_USDT",
                    "https://www.binance.com/en/trade/SOL_USDT",
                ],
            },
            {
                "split" : "3-bottom",
                "urls" : [
                    "https://www.binance.com/en/trade/BTC_USDT",
                    "https://www.binance.com/en/trade/ETH_USDT",
                    "https://www.binance.com/en/trade/SOL_USDT",
                ],
            },
            {
                "split" : "4",
                "urls" : [
                    "http://localhost:9000/coin-village-bucket/eda/volume_imbalance_time/KRW-BTC/3w.png",
                    "http://localhost:9000/coin-village-bucket/eda/volume_imbalance_time/KRW-BTC/1m.png",
                    "http://localhost:9000/coin-village-bucket/eda/volume_imbalance_time/KRW-BTC/2m.png",
                    "http://localhost:9000/coin-village-bucket/eda/volume_imbalance_time/KRW-BTC/3m.png",
                ],
            }
        ]
        self.rotate_term = 300
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

                    # if keyboard.is_pressed("space") and keyboard.is_pressed("right"):
                    #     print(">> 다음 그룹")
                    #     index = (index + 1) % len(self.groups)
                    #     break

                    # if keyboard.is_pressed("space") and keyboard.is_pressed("left"):
                    #     print(">> 이전 그룹")
                    #     index = (index - 1) % len(self.groups)
                    #     break

                    if time.time() - start_time >= self.rotate_term:
                        index = (index + 1) % len(self.groups)
                        break

                    time.sleep(1)

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

    def handle(self, cmd):

        if cmd == "NEXT":
            index = (index + 1) % len(groups)
            print(">> 다음 그룹", index)

        elif cmd == "PREV":
            index = (index - 1) % len(groups)
            print(">> 이전 그룹", index)

rotate_urls = RotateUrls()
rotate_urls.main()