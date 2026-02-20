from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule

from background.dao.heatmaps_dao import HeatmapsDao

from background.modules.log import Log
from background.modules.redis import r as redis_single

import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
import os

import datetime

class CvResearchProd01Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd01Gen01
    Generation : 01 
    
    Desc : 
    - heatmaps_volume_time_week
    """
    pref_slack_msg_box = ""

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        super().__init__(interval_options, schedule_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = redis_single
        self.upbit = ExChangeUpbit()
        self.minio = MinioModule()

        self.heamap_dao = HeatmapsDao()

        self.tickers = self.service_options.get("tickers")
        self.ticker = None
    
    def main(self):

        try:
            for ticker in self.tickers:
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.gen_heatmap()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def gen_heatmap(self):

        interval = "minute5"
        count = 200
        days = 93

        end_dt = datetime.datetime.now()
        start_dt = end_dt - datetime.timedelta(days=days)

        dfs = []
        to = end_dt
        max_call = int((days * 24 * 12) / count) + 2

        # --- df 생성
        for _ in range(max_call):
            df = self.upbit.get_ohlcv(
                interval=interval,
                date=to.strftime("%Y-%m-%d %H:%M:%S"),
                count=count
            )

            if df is None or df.empty:
                break

            dfs.append(df)

            oldest_dt = df["datetime"].iloc[0]

            # 30일 이전이면 종료
            if oldest_dt <= start_dt:
                break

            # 다음 호출 기준점
            to = oldest_dt - datetime.timedelta(minutes=5)

        # --- df 콘켓
        df_combined = (
            pd.concat(dfs)
            .drop_duplicates(subset="datetime")
            .sort_values("datetime")
            .reset_index(drop=True)
        )

        # --- 파생변수
        # 1. timestamp 컬럼 datetime 변환 (unit='s' 또는 'ms' 꼭 지정)
        df_combined["timestamp"] = df_combined["datetime"].astype("int64") // 10**9
        df_combined['timestamp'] = pd.to_datetime(df_combined['timestamp'], unit='s')

        # 2. 시간대 추출 (예: 시(hour))
        df_combined['hour'] = df_combined['timestamp'].dt.hour
        df_combined['minute'] = df_combined['timestamp'].dt.minute

        # 요일 (문자)
        df_combined["weekday"] = df_combined["datetime"].dt.day_name()

        # 요일 (숫자: 월=0 ~ 일=6)
        df_combined["weekday_num"] = df_combined["datetime"].dt.weekday

        # 다음 종가
        df_combined["next_close"] = df_combined["close"].shift(-1)

        # 변화량 (미래 - 현재)
        df_combined["future_change"] = df_combined["next_close"] - df_combined["close"]

        # 변화율 (%)
        df_combined["future_change_pct"] = (df_combined["future_change"] / df_combined["close"]) * 100

        # 방향
        df_combined["future_direction"] = df_combined["future_change_pct"].apply(
            lambda x: "UP" if x > 0 else ("DOWN" if x < -0 else "FLAT")
        )

        df_combined["future_direction_num"] = df_combined["future_change_pct"].apply(
            lambda x: 1 if x > 0 else (-1 if x < -0 else 0)
        )

        # 방향성 거래량
        df_combined["signed_volume"] = df_combined["volume"] * df_combined["future_direction_num"]

        # 양/음 거래량 분리
        df_combined["pos_volume"] = df_combined["signed_volume"].apply(lambda x: x if x > 0 else 0)
        df_combined["neg_volume"] = df_combined["signed_volume"].apply(lambda x: abs(x) if x < 0 else 0)

        df_combined["volume_delta"] = df_combined["pos_volume"] - df_combined["neg_volume"]

        df_combined["volume_imbalance"] = (
            df_combined["pos_volume"] - df_combined["neg_volume"]
        ) / (
            df_combined["pos_volume"] + df_combined["neg_volume"] + 1e-9
        )
        
        # --- 일자별로 컷하여 업로드
        df_2w  = self.cut_by_days(df_combined, end_dt, 14)
        df_3w  = self.cut_by_days(df_combined, end_dt, 21)
        df_1m  = self.cut_by_days(df_combined, end_dt, 30)
        df_2m  = self.cut_by_days(df_combined, end_dt, 60)
        df_3m  = df_combined

        self.upload_to_minio(df_2w, "2w")
        self.upload_to_minio(df_3w, "3w")
        self.upload_to_minio(df_1m, "1m")
        self.upload_to_minio(df_2m, "2m")
        self.upload_to_minio(df_3m, "3m")
    
    def cut_by_days(self, df, target_date, days):
        start = target_date - datetime.timedelta(days=days)
        return df[df["datetime"] >= start].copy()
    
    def upload_to_minio(self, df, term):

        try:
            pivot_vol = df.pivot_table(
                values="volume_imbalance",
                index="hour",
                columns="weekday",
                aggfunc="mean"
            )

            plt.figure(figsize=(12, 6))
            sns.heatmap(pivot_vol, annot=True, fmt=".2f", cmap="coolwarm", center=0)
            plt.title("Time x Week Volume Imbalance Heatmap")

            # 저장경로 설정
            local_path = self.minio.generate_local_path("png")
            minio_path = f"heat_map/time_week_updown_rate_heat_map/{self.ticker}/{term}_time_week_updown_rate_heat_map.png"

            # 로컬에 저장
            plt.savefig(
                local_path,
                dpi=300,
                bbox_inches="tight"
            )

            plt.close() 

            # 업로드
            self.minio.upload_file(minio_path, local_path)

            # db 경로 저장
            params = {}
            params["ticker"] = self.ticker
            params["term"] = term
            params["minio_path"] = minio_path
            self.heamap_dao.upsert_heatmaps_volume_time_week(params)
        
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

        finally:
            if os.path.exists(local_path):
                os.remove(local_path)
    