from background.modules.log import system_module_log
from background.dao.runnable_services_dao import *
from background.functions.common_function import find_target_dictionary 

import importlib
import multiprocessing
import time

import signal

import os, sys
import inspect

class ProcessHandler():
    """
    def description : 프로세스 핸들러
    
    - 실행해야할 프로세스, 킬 해야할 프로세스를 DB를 토대로 실시간 핸들링
    
    """

    def __init__(self):
        self.log = system_module_log
        self.runnable_services_dao = runnableServicesDao()
        
        self.processes = {}
            
    def run_handler(self):
        
        while True:
            
            # --- 데이터 셋팅
            runnable_services = self.runnable_services_dao.get_runnable_services()
            
            seq_current_processes = list(self.processes.keys())                         # 현재 실행 중인 프로세스 시퀀스
            seq_runnable_services = [d['seq'] for d in runnable_services if 'seq' in d] # 실행 해야할 프로세스 시퀀스
            
            # --- 모든 시퀀스가 같지 않으면 
            if sorted(seq_current_processes) != sorted(seq_runnable_services):
                
                include_seqs = list(set(seq_runnable_services) - set(seq_current_processes)) # 추가 대상 시퀀스
                exclude_seqs = list(set(seq_current_processes) - set(seq_runnable_services)) # 제외 대상 시퀀스
                    
                # 1. 추가 된 프로세스 시작 
                if len(include_seqs) > 0:
                    for include_seq in include_seqs:
                        runnable_service = find_target_dictionary("seq", include_seq, runnable_services)
                        self.start_process(
                            include_seq, 
                            runnable_service["execution_path"], 
                            runnable_service["execution_class"], 
                            runnable_service["execution_method"], 
                            runnable_service["service_options"]
                        )
                
                # 2. 제외 된 프로세스 종료
                if len(exclude_seqs) > 0:
                    for exclude_seq in exclude_seqs:
                        self.kill_process(exclude_seq)
            
            time.sleep(1) 
    
    def start_process(self, seq, execution_path, execution_class, execution_method, service_options=None):
        
        # --- 프로세스 실행
        if seq in self.processes and self.processes[seq].is_alive():
            return
        
        try:
            # 캐싱 무효화
            if execution_path in sys.modules:
                del sys.modules[execution_path]
                
            # 파일 임포트, 클래스, 메소드 동적 호출
            service_module = importlib.import_module(f"{execution_path}")
            service_class = getattr(service_module, execution_class)
            if service_options:
                service_method = getattr(service_class(seq, service_options), execution_method)
            
            else:
                service_method = getattr(service_class(seq), execution_method)
                
            p = multiprocessing.Process(target=service_method)
            p.start()

            self.processes[seq] = p 
            self.log.info(f"프로세스 로딩 성공. seq : {seq}, execute file : {execution_path}, class & method : {execution_class}.{execution_method}")
            
        except Exception as e:
            self.log.info(f"프로세스 로딩 실패. seq : {seq}, execute file : {execution_path}, class & method : {execution_class}.{execution_method}, error : {e}")
    
    def kill_process(self, seq):
        
        if seq not in self.processes:
            return
        
        try:
            self.processes[seq].terminate()
            self.processes[seq].join(timeout=10) 
            
            if self.processes[seq].is_alive():
                os.kill(self.processes[seq].pid, signal.SIGKILL)  
            
            del self.processes[seq]
            
            self.log.info(f"프로세스 킬 성공. seq : {seq}")
            
        except Exception as e:
            self.log.info(f"프로세스 킬 실패. {seq}, class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            