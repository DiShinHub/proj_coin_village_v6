from background.modules.log import system_module_log
from background.config.config import Config

import json
import inspect

class Redis():

    def __init__(self):
        self.log = system_module_log
        self.redis = Config().set_redis() 
        
        self.pref_slack_msg_box = "slack_msg_box"
    
    def get_conn(self):
        return self.redis

    def get_keys(self, match, count):

        try : 
            match = f"*{match}*"

            key_list = []
            for key in self.redis.scan_iter(match, count):
                key_list.append(str(key.decode('utf-8')))

            return key_list

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def set_data(self, key, val, expire):

        try : 
            self.redis.set(key, val, expire)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def get_data(self, key):

        try : 
            data = self.redis.get(key)
            if data is None:
                return {}

            ttl = self.redis.ttl(key)
            data_dict = {
                "val" : str(data.decode('utf-8')),
                "expire" : str(ttl)
            }
            return data_dict
    
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def get_json_data(self, key):

        try : 
            data = self.redis.get(key)
            if data is None:
                return {}
            
            val = json.loads(data.decode('utf-8'))
            return val
    
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def update_data(self, key, val, expire):

        try : 
            if self.redis.get(key):
                self.redis.delete(key)

            self.redis.set(key, val, expire)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def delete_data(self, key):

        try : 
            if self.get_data(key):
                self.redis.delete(key)
        
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise
    
    def hset_data(self, key, field, val):

        try : 
            if key and field and val:
                self.redis.hset(key, field, val)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def hget_data(self, key, field):

        try : 
            data = self.redis.hget(key, field)
            if data is None:
                return None
            
            return bytes.decode(data)
    
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def hgetall_data(self, key):

        try : 

            data = self.redis.hgetall(key)
            if data is None:
                return None

            # 이진 데이터를 문자열로 변환하고 딕셔너리를 생성
            result = {field.decode('utf-8'): value.decode('utf-8') for field, value in data.items()}
            return result
    
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def hget_json_data(self, key, field):

        try : 
            data = self.redis.hget(key, field)
            if data is None:
                return {}
            
            val = json.loads(data.decode('utf-8'))
            return val
    
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def hdel_data(self, key, field):
        
        try : 
            if self.redis.hget(key, field):
                self.redis.hdel(key, field)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise
    
    def hupd_date(self, key, field, val):   

        try : 
            #self.hdel_data(key, field)
            if key and field and val:
                self.hset_data(key, field, val)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise
        
    def lpush(self, key, val, ttl=None):

        try : 
            if key and val:
                self.redis.lpush(key, val)
                if ttl:
                    self.redis.expire(key, ttl) 

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

        return 
    
    def lrange_all(self, key):

        try : 
            if key:
                return self.redis.lrange(key, 0, -1)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

        return 
    
    def lpop(self, key):

        try : 
            if key:
                self.redis.lpop(key)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise

    def flushall(self):

        try : 
            self.redis.flushdb()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
            raise
    
    def replace_hyphen(self, target):

        if "-" in target:
            return target.replace("-", "_")

        return target

    def save_msg_on_Q(self, msg, type=None):
        """ 
        def description : 슬랙 메세지 전송을 위해 레디스에 데이터 삽입

        Parameters
        ----------
        msg : 메세지
        type : 메세지 타입

        Returns
        -------
        response_object : 결과 오브젝트 (dict)
        """

        self.redis.lpush(self.pref_slack_msg_box, msg)

        response_object = {
            "status": "success",
            "message": "success"
        }
        return response_object
            
# use single ton
r = Redis()
redis_client = r.get_conn()