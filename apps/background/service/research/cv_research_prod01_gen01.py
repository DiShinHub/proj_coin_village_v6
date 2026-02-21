from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.exchange__calculator import ExChangeCalculator
from background.modules.minio import MinioModule

from background.dao.heatmaps_dao import HeatmapsDao

from background.modules.log import Log
from background.modules.redis import r as redis_single


from sklearn.ensemble import RandomForestClassifier

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
    
    def set_data(self):

        self.interval = "minute5"
        self.count = 200
        self.days = 93

        self.end_dt = datetime.datetime.now()
        self.start_dt = self.end_dt - datetime.timedelta(days=self.days)

    def gen_df(self):
        dfs = []
        to = self.end_dt
        max_call = int((self.days * 24 * 12) / self.count) + 2

        # --- df 생성
        for _ in range(max_call):
            df = self.upbit.get_ohlcv(
                interval=self.interval,
                date=to.strftime("%Y-%m-%d %H:%M:%S"),
                count=self.ount
            )

            if df is None or df.empty:
                break

            dfs.append(df)

            oldest_dt = df["datetime"].iloc[0]

            # 30일 이전이면 종료
            if oldest_dt <= self.start_dt:
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
        return df_combined

    def gen_heatmap_volumn_time(self, df_combined):

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
        
        df_1w  = self.cut_by_days(df_combined, self.end_dt, 7)
        df_2w  = self.cut_by_days(df_combined, self.end_dt, 14)
        df_3w  = self.cut_by_days(df_combined, self.end_dt, 21)
        df_1m  = self.cut_by_days(df_combined, self.end_dt, 30)
        df_2m  = self.cut_by_days(df_combined, self.end_dt, 60)
        df_3m  = df_combined

        self.upload_heatmap_volumn_time(df_1w, "1w")
        self.upload_heatmap_volumn_time(df_2w, "2w")
        self.upload_heatmap_volumn_time(df_3w, "3w")
        self.upload_heatmap_volumn_time(df_1m, "1m")
        self.upload_heatmap_volumn_time(df_2m, "2m")
        self.upload_heatmap_volumn_time(df_3m, "3m")
    
    def upload_heatmap_volumn_time(self, df, term):

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
    
    def gen_feature_importances(self, df_combined):
        calculator = ExChangeCalculator(df_combined)
        df = self.apply_all_features(calculator)
        df = self.create_target(df, horizon=3)  # 15분 뒤 기준

        df_1w  = self.cut_by_days(self.end_dt, df, 7)
        df_2w  = self.cut_by_days(self.end_dt, df, 14)
        df_3w  = self.cut_by_days(self.end_dt, df, 21)
        df_1m  = self.cut_by_days(self.end_dt, df, 30)
        df_2m  = self.cut_by_days(self.end_dt, df, 60)
        df_3m  = df

        df_1w = self.get_feature_importance(df_1w)
        df_2w = self.get_feature_importance(df_2w)
        df_3w = self.get_feature_importance(df_3w)
        df_1m = self.get_feature_importance(df_1m)
        df_2m = self.get_feature_importance(df_2m)
        df_3m = self.get_feature_importance(df_3m)
        
        self.upload_feature_importances(df_1w, "1w")
        self.upload_feature_importances(df_2w, "2w")
        self.upload_feature_importances(df_3w, "3w")
        self.upload_feature_importances(df_1m, "1m")
        self.upload_feature_importances(df_2m, "2m")
        self.upload_feature_importances(df_3m, "3m")
    
    def upload_feature_importances(self, df, term):

        try:
            plt.figure(figsize=(10, 8))
            sns.barplot(
                x="importance",
                y="feature",
                data=df,
                orient="h"
            )
            
            plt.title("feature & importance of UP x DOWN x SIDEAWAY Heatmap")
            plt.tight_layout()
            
            # 저장경로 설정
            local_path = self.minio.generate_local_path("png")
            minio_path = f"heat_map/feature_importace_updown_rate_heat_map/{self.ticker}/{term}_feature_importace_updown_rate_heat_map.png"

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


    def apply_all_features(self, calculator):
        methods = [
            getattr(calculator, m)
            for m in dir(calculator)
            if callable(getattr(calculator, m))
            and m.startswith("set_")
            and m not in ["set_ohlcv"]
        ]
        
        for method in methods:
            try:
                method()
            except Exception:
                pass

        return calculator.get_df()

    def create_target(self, df, horizon=12):  # 예: minute5 기준 12 = 1시간
        df = df.copy()
        df["future_close"] = df["close"].shift(-horizon)
        df["return"] = (df["future_close"] - df["close"]) / df["close"]

        df["target"] = 0
        df.loc[df["return"] >= 0.005, "target"] = 1
        df.loc[df["return"] <= -0.005, "target"] = -1

        #df = df.dropna()
        return df

    def get_feature_importance(self, df):

        df = df.copy()

        X = df.drop(columns=["datetime", "target", "future_close", "return"], errors="ignore")
        y = df["target"]

        X = X.select_dtypes(include=[np.number])
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)

        valid_idx = X.index.intersection(y.index)
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]

        if len(y.unique()) < 2:
            print("⚠ target class 부족")
            return None

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced"
        )

        model.fit(X, y)

        importance = pd.DataFrame({
            "feature": X.columns,
            "importance": model.feature_importances_
        }).sort_values(by="importance", ascending=False)

        return importance.head(30)

    def cut_by_days(self, df, target_date, days):
        start = target_date - datetime.timedelta(days=days)
        return df[df["datetime"] >= start].copy()





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
        df_1w  = self.cut_by_days(df_combined, end_dt, 7)
        df_2w  = self.cut_by_days(df_combined, end_dt, 14)
        df_3w  = self.cut_by_days(df_combined, end_dt, 21)
        df_1m  = self.cut_by_days(df_combined, end_dt, 30)
        df_2m  = self.cut_by_days(df_combined, end_dt, 60)
        df_3m  = df_combined

        self.upload_to_minio(df_1w, "1w")
        self.upload_to_minio(df_2w, "2w")
        self.upload_to_minio(df_3w, "3w")
        self.upload_to_minio(df_1m, "1m")
        self.upload_to_minio(df_2m, "2m")
        self.upload_to_minio(df_3m, "3m")