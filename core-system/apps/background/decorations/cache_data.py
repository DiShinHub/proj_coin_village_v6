from background.modules.log import system_module_log
from background.modules.redis import redis_client 

from functools import wraps
import json
import inspect
import pandas as pd
        
def cache_data(key_template="{class_name}|{class_attr}|{func_name}|{kwargs_repr}", ttl=1):
    """
    def description : Redis를 활용한 동적 캐싱 데코레이터 

    Parameters
    ----------
    key_template : 키 생성 템플릿 
    ttl : 캐시 만료 시간(초 단위)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # 클래스명, 클래스 속성, 메소드명, 파라미터 추출
            self_instance = args[0]
            class_name = self_instance.__class__.__name__
            class_attr = {attr_name: attr_value for attr_name, attr_value in vars(self_instance).items() if isinstance(attr_value, str)}
            func_name = func.__name__
            #kwargs_repr = json.dumps(kwargs if kwargs else {}, sort_keys=True, default=str)
            
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            all_kwargs = dict(bound.arguments)
            all_kwargs.pop("self", None)
            kwargs_repr = json.dumps(all_kwargs, sort_keys=True, default=str)
            
            # 동적 캐시 키 생성
            cache_key = key_template.format(
                class_name=class_name,
                class_attr=class_attr,
                func_name=func_name,
                kwargs_repr=kwargs_repr
            )
            cache_key = cache_key.replace("'", "\"")
            
            # --- Redis HIT, MISS 처리
            cache_data = None
            try:
                cache_data = redis_client.get(cache_key)
                # HIT
                if cache_data is not None:
                    payload = json.loads(cache_data)
                    if payload["type"] == "df":
                        cache_data = pd.read_json(payload["data"])
                        return pd.read_json(payload["data"])

                    else:
                        cache_data = json.loads(payload["data"])
                        return cache_data

                # MISS
                cache_data = func(*args, **kwargs) 
                return cache_data
                
            except Exception as e:
                system_module_log.info(f"method : {str(func.__name__)}, error : {str(e)}")
                raise e
            
            finally:
                if isinstance(cache_data, pd.DataFrame): 
                    if not cache_data.empty: 
                        payload = {
                            "type": "df",
                            "data": cache_data.to_json()
                        }
                        redis_client.psetex(cache_key, int(ttl*1000), json.dumps(payload).encode('utf-8'))

                else:
                    if cache_data:
                        if isinstance(cache_data, (dict, list)):
                            payload = {
                                "type": "json",
                                "data": json.dumps(cache_data).encode('utf-8')
                            }
                            redis_client.psetex(cache_key, int(ttl*1000), json.dumps(payload).encode('utf-8'))

                        elif isinstance(cache_data, str):
                            payload = {
                                "type": "json",
                                "data": cache_data.encode('utf-8')
                            }
                            redis_client.psetex(cache_key, int(ttl*1000), json.dumps(payload).encode('utf-8'))

                        elif isinstance(cache_data, bytes):
                            payload = {
                                "type": "json",
                                "data": cache_data
                            }
                            redis_client.psetex(cache_key, int(ttl*1000), json.dumps(payload).encode('utf-8'))

                        else:
                            payload = {
                                "type": "json",
                                "data": cache_data
                            }
                            redis_client.psetex(cache_key, int(ttl*1000), json.dumps(payload).encode('utf-8'))
        
        return wrapper
    return decorator