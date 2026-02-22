import logging
import os

class Log():
    
    def __init__(self, file_name):
        
        self.logger = None
        self.create_log(
            log_path = f"./logs/{(file_name).split('.')[0]}", 
            log_name = f"{(file_name).split('.')[0]}"
        )
         
    def create_log(self, log_path=None, log_name=None):
        """ 
        def description : 로그 생성

        Parameters
        ----------
        log_path = 로그 경로
        log_name = 로그 이름
        """
        
        # logger 셋팅
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)

        # logger 출력 형식
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # logger 출력 핸들러
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            self.logger.addHandler(stream_handler)

        if not os.path.isdir(f'{log_path}/'):
            os.mkdir(f'{log_path}/')

        # logger 파일 핸들러
        file_path = log_path + "/" + log_name + ".log"
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        if not any(isinstance(handler, logging.FileHandler) for handler in self.logger.handlers):
            self.logger.addHandler(file_handler)
        
        return self.logger
    
    def get_logger(self):
        return self.logger
    
# single tons
logger = Log("logger").get_logger()

