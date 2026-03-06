from background.modules.log import system_module_log
from functools import wraps
import time

def try_again(num):
    """
    def description : 재시도 wrapper

    Parameters
    ----------
    num : 재시도 카운트(int)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(num):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    if attempt < num - 1:
                        time.sleep(1)
                        continue

                    else:
                        system_module_log.info(f"method : {str(func.__name__)}, All retries failed, error : {str(e)}")
                        raise Exception(f"All retries failed, error : {str(e)}")
                    
        return wrapper
    return decorator