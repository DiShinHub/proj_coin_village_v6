from modules.log import logger

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tkinter as tk

class Seleniums:

    def __init__(self):
        self.log = logger

    def get_screen_size(self):
        root = tk.Tk()
        root.withdraw()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height

    def get_layout(self, screen_width, screen_height, split="4"):

        w = screen_width
        h = screen_height

        if split == "1":
            return [(0, 0, w, h)]

        if split == "2-h":  # 좌우
            return [
                (0, 0, w//2, h),
                (w//2, 0, w//2, h)
            ]

        if split == "2-v":  # 상하
            return [
                (0, 0, w, h//2),
                (0, h//2, w, h//2)
            ]

        if split == "3-top":  # 위1 + 아래2
            return [
                (0, 0, w, h//2),
                (0, h//2, w//2, h//2),
                (w//2, h//2, w//2, h//2)
            ]

        if split == "3-bottom":  # 아래1 + 위2
            return [
                (0, 0, w//2, h//2),
                (w//2, 0, w//2, h//2),
                (0, h//2, w, h//2)
            ]

        if split == "4":
            return [
                (0, 0, w//2, h//2),
                (w//2, 0, w//2, h//2),
                (0, h//2, w//2, h//2),
                (w//2, h//2, w//2, h//2)
            ]
    
    def create_driver(self, x, y, width, height):
        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(options=options)
        driver.set_window_position(x, y)
        driver.set_window_size(width, height)

        return driver