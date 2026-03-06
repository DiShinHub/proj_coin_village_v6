from background.modules.log import system_module_log
from background.dao.reuse_data_dao import reuse_data_dao
from background.functions.common_function import parse_and_convert_string 

from functools import wraps
import json

def reuse_data(key_template="{class_name}|{class_attr}|{func_name}|{kwargs_repr}", required_keys=None):
    """
    def description : Postgres를 활용한 데이터 재사용 데코레이터
    
    kwargs에 required_keys에 해당하는 키가 존재하면 재사용 실행, 없으면 무시하고 원본을 실행

    Parameters
    ----------
    key_template : 키 생성 템플릿
    required_keys : 재사용에 요구되는 키
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # 데이터 셋팅 
            reuse_data = None
            
            self_instance = args[0]
            class_name = self_instance.__class__.__name__
            class_attr = {attr_name: attr_value for attr_name, attr_value in vars(self_instance).items() if isinstance(attr_value, str)}
            func_name = func.__name__
            kwargs_repr = json.dumps(kwargs if kwargs else {}, sort_keys=True, default=str)
            
            # --- 파라미터의 키가 required_keys에 부합하지 않으면 원본 함수를 실행
            if required_keys:
                if not all(key in kwargs_repr for key in required_keys):
                    return func(*args, **kwargs) 
            
            # --- 동적 키 생성
            reuse_key = key_template.format(
                class_name=class_name,
                class_attr=class_attr,
                func_name=func_name,
                kwargs_repr=kwargs_repr
            )
            reuse_key = reuse_key.replace("'", "\"")

            # --- Postgres HIT, MISS 처리
            try:
                reuse_data = reuse_data_dao.read_reusable_data(reuse_key)
                if reuse_data: # HIT
                    reuse_data_dao.update_reusable_data(reuse_key)
                    reuse_data = parse_and_convert_string(reuse_data)
                    return reuse_data

                reuse_data = func(*args, **kwargs) # MISS
                return reuse_data
                
            except Exception as e:
                system_module_log.info(f"method : {str(func.__name__)}, error : {str(e)}")
                raise e
            
            finally:
                if reuse_data:
                    if isinstance(reuse_data, (dict, list)):
                        reuse_data = json.dumps(reuse_data)

                    elif isinstance(reuse_data, bytes):
                        reuse_data = reuse_data.decode('utf-8')
                        
                    reuse_data_dao.upsert_reusable_data(reuse_key, str(reuse_data))
        
        return wrapper
    return decorator