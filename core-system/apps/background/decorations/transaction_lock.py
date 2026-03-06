from background.modules.log import system_module_log
from background.modules.redis import redis_client 

from functools import wraps

import time
    
def lock_transaction(lock_key, ttl=10, hold=0):
    """
    def description : 트랜잭션 락
    
    주요 트랜잭션 테스크 수행 중에 다른 테스크의 수행을 중단
    
    Parameters
    ----------
    lock_key : 락키
    ttl : expire 시간
    hold : 트랜잭션 종료 후 대기시간
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # 논리적 충돌 방지를 위한 트릭킹 
            time.sleep(0.375)
            if redis_client.exists(lock_key):
                raise Exception(f"blocked by overlab transaction, block type")
            
            try:
                
                # lock transaction
                res = redis_client.set(lock_key, "1", ttl, nx=True) # nx: key가 없을 때만 set을 할 수 있다
                
                if res == True:
                    # execute transaction
                    return func(*args, **kwargs)
                
                else:
                    raise Exception(f"blocked by overlab transaction, block type")
                
            except Exception as e:
                system_module_log.info(f"method : {str(func.__name__)}, error : {str(e)}")
                raise e 
            
            finally:
                
                # hold transaction
                if isinstance(hold, int):
                    if hold > 0:
                        time.sleep(hold) 
                        
                # unlock transaction
                redis_client.delete(lock_key)
                
        return wrapper
    return decorator

def wait_when_lock(lock_key):
    """
    def description : 트랜잭션 락일 때 웨이팅
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            try:
                cnt = 0 
                while cnt < 10:
                    if not redis_client.exists(lock_key):
                        return func(*args, **kwargs)
                    
                    else:
                        cnt += 1
                        time.sleep(1)
                     
            except Exception as e:
                system_module_log.info(f"method : {str(func.__name__)}, error : {str(e)}")
                raise e
                
        return wrapper
    return decorator
        
def block_when_lock(lock_key):
    """
    def description : 트랜잭션 락일 떄 블로킹
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            try:
                if redis_client.exists(lock_key):
                    raise Exception(f"blocked by transaction lock")
                
                return func(*args, **kwargs)
                     
            except Exception as e:
                system_module_log.info(f"method : {str(func.__name__)}, error : {str(e)}")
                raise e
                
        return wrapper
    return decorator
