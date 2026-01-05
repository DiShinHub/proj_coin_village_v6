from background.modules.log import system_module_log
from background.config.config import Config
from background.decorations.try_again import try_again
from background.decorations.cache_data import cache_data
from background.decorations.reuse_data import reuse_data

from background.modules.exchange__calculator import ExChangeCalculator

from datetime import datetime, timedelta
import inspect

class ExChangeKIS(ExChangeCalculator):

    def __init__(self):
        self.log = system_module_log
        config = Config()

    def set_ticker(self, ticker):
        self.ticker = ticker
        return True

    def get_ticker(self):
        return self.ticker
    
    def form_ohlcv(self):
        pass