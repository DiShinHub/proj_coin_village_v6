

from background.functions.common_function import *

from psycopg2 import pool
import redis
from minio import Minio
import slack_sdk

import pyupbit
from binance.client import Client

import sys
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
        
    def set_redis(self):
        
        with redis.StrictRedis(host=os.getenv('REDIS_HOST'), 
                               port=int(os.getenv('REDIS_PORT')), 
                               db=os.getenv('REDIS_DB')) as conn:
            redis_conn = conn
            
        return redis_conn
        
    def set_postgres(self):

        # Create a connection pool
        connection_pool = pool.ThreadedConnectionPool(
            1, 30, 
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            user=os.getenv("POSTGRES_USER"),  
            password=os.getenv("POSTGRES_PASSWORD"),  
        )
        return connection_pool
    
    def set_minio(self):

        # self.internal_client = Minio(
        #     f'{os.getenv("MINIO_INTERNAL_URL")}',
        #     access_key=os.getenv("MINIO_ACCESS_KEY"),
        #     secret_key=os.getenv("MINIO_SECRET_KEY"),
        #     secure=False,
        # )

        external_client = Minio(
            f"{os.getenv('MINIO_EXTERNAL_URL')}:{os.getenv('MINIO_SERVICE_PORT')}",
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )
        minio_bucket = os.getenv("MINIO_BUCKET")
        minio_local = f'{sys.path[0]}/{os.getenv("MINIO_LOCAL")}'

        return external_client, minio_bucket, minio_local

    def set_slack(self):
        
        slack_client = slack_sdk.WebClient(token=os.getenv("SLACK_TOKEN"))
        return slack_client
    
    def set_upbit(self):

        upbit = pyupbit.Upbit(
            os.getenv("UPBIT_ACCESS_KEY"),
            os.getenv("UPBIT_SECRET_KEY")
        )
        upbit = upbit

        return upbit

    def set_binance(self):

        binance_access_key = os.getenv("BINANCE_ACCESS_KEY")
        binance_secret_key = os.getenv("BINANCE_SECRET_KEY")

        # 바이낸스 클라이언트 생성
        client = Client(binance_access_key, binance_secret_key)

        return client
    
    def set_kis(self):

        kis_app_key = os.getenv("KIS_APP_KEY")
        kis_secret_key = os.getenv("KIS_SECRET_KEY")
        return kis_app_key, kis_secret_key

    def set_exchange_rate(self):
        
        exchage_rate_key = os.getenv("EXCHAGE_RATE_KEY")
        return exchage_rate_key
    
    def set_notion(self):
        
        notion_key = os.getenv("NOTION_KEY")
        return notion_key
        
        