from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.minio import MinioModule
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.eda_dao import EdaDao

from sklearn.ensemble import RandomForestClassifier
import shap

import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
import os

import datetime

class CvVisualizerProd01Gen01(ServiceHandler):
    """
    Service Name : CvVisualizerProd01Gen01
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

        self.eda_dao = EdaDao()

        self.tickers = self.service_options.get("tickers")
        self.ticker = None
    
    def main(self):

        try:
            for ticker in self.tickers:
                
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.paint_eda()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def paint_eda(self):

        interval_ = "minute5"
        days = 93
        count = 200
        to_ = datetime.datetime.now()
        from_ = to_ - datetime.timedelta(days=days)

        self.upbit.set_ohlcvs(
            interval=interval_, 
            days=days, 
            count=count, 
            from_=from_, 
            to_=to_
        )

        df = self.upbit.set_all_features()

        df_1w  = self.cut_by_days(df, to_, 7)
        df_2w  = self.cut_by_days(df, to_, 14)
        df_3w  = self.cut_by_days(df, to_, 21)
        df_1m  = self.cut_by_days(df, to_, 30)
        df_2m  = self.cut_by_days(df, to_, 60)
        df_3m  = df
        
        self.upload_volume_imbalance_time(df_1w, "1w")
        self.upload_volume_imbalance_time(df_2w, "2w")
        self.upload_volume_imbalance_time(df_3w, "3w")
        self.upload_volume_imbalance_time(df_1m, "1m")
        self.upload_volume_imbalance_time(df_2m, "2m")
        self.upload_volume_imbalance_time(df_3m, "3m")

        self.upload_feature_importance(df_1w, "1w")
        self.upload_feature_importance(df_2w, "2w")
        self.upload_feature_importance(df_3w, "3w")
        self.upload_feature_importance(df_1m, "1m")
        self.upload_feature_importance(df_2m, "2m")
        self.upload_feature_importance(df_3m, "3m")

    
    def upload_volume_imbalance_time(self, df, term):
        
        local_path = None
        try:
            if "volume_imbalance" not in df.columns:
                for col in df.columns:
                    self.log.info(col)

            pivot_vol = df.pivot_table(
                values="volume_imbalance",
                index="hour",
                columns="weekday",
                aggfunc="mean"
            )

            plt.figure(figsize=(12, 6))
            sns.heatmap(pivot_vol, annot=True, fmt=".2f", cmap="coolwarm", center=0)
            plt.title("Time x Volume Imbalance of UP x DOWN x SIDEAWAY")

            # 저장경로 설정
            local_path = self.minio.generate_local_path("png")
            minio_path = f"eda/volume_imbalance_time/{self.ticker}/{term}.png"

            # 로컬에 저장
            plt.savefig(
                local_path,
                dpi=300,
                bbox_inches="tight"
            )

            plt.close() 

            # 업로드
            self.minio.upload_file(
                minio_file_path = minio_path, 
                local_file_path = local_path, 
                content_type = "image/png", 
                metadata = {
                    "Content-Disposition": "inline"
                })
            
            # db 경로 저장
            params = {}
            params["exchange"] = "upbit"
            params["ticker"] = self.ticker
            params["minio_path"] = minio_path
            params["description"] = ""
            self.eda_dao.upsert_eda_images(params)
        
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

        finally:
            if local_path:
                if os.path.exists(local_path):
                    os.remove(local_path)

    def upload_feature_importance(self, df, term):

        try:
            importance = self.get_feature_importance(df)

            plt.figure(figsize=(10, 8))
            sns.barplot(
                x="importance",
                y="feature",
                data=importance,
                orient="h"
            )
            
            plt.title("Feature importance of UP x DOWN x SIDEAWAY")
            plt.tight_layout()
            
            # 저장경로 설정
            local_path = self.minio.generate_local_path("png")
            minio_path = f"eda/feature_importance/{self.ticker}/{term}.png"

            # 로컬에 저장
            plt.savefig(
                local_path,
                dpi=300,
                bbox_inches="tight"
            )
            plt.close() 

            # 업로드
            self.minio.upload_file(
                minio_file_path = minio_path, 
                local_file_path = local_path, 
                content_type = "image/png", 
                metadata = {
                    "Content-Disposition": "inline"
                })

            # db 경로 저장
            params = {}
            params["exchange"] = "upbit"
            params["ticker"] = self.ticker
            params["minio_path"] = minio_path
            params["description"] = ""
            self.eda_dao.upsert_eda_images(params)
        
        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

        finally:
            if os.path.exists(local_path):
                os.remove(local_path)
                
    def upload_feature_importance_shap(self, df, term):

        try:
            up, down = self.get_feature_importance_shap(df)

            up = up.copy()
            down = down.copy()

            up["direction"] = "UP"
            down["direction"] = "DOWN"

            result = pd.concat([up, down])

            plt.figure(figsize=(10, 8))

            sns.barplot(
                x="mean_shap",
                y="feature",
                hue="direction",
                data=result,
                dodge=False
            )

            plt.title("Feature Direction (UP vs DOWN)")
            plt.tight_layout()

            # 저장경로
            local_path = self.minio.generate_local_path("png")
            minio_path = f"eda/feature_direction/{self.ticker}/{term}.png"

            # 로컬 저장
            plt.savefig(
                local_path,
                dpi=300,
                bbox_inches="tight"
            )
            plt.close()

            # 업로드
            self.minio.upload_file(
                minio_file_path=minio_path,
                local_file_path=local_path,
                content_type="image/png",
                metadata={
                    "Content-Disposition": "inline"
                })

            # DB 저장
            params = {}
            params["exchange"] = "upbit"
            params["ticker"] = self.ticker
            params["minio_path"] = minio_path
            params["description"] = "feature direction (shap)"
            self.eda_dao.upsert_eda_images(params)

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")

        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    def get_feature_importance(self, df):

        df = df.copy()

        X = df.drop(columns=["future_close", "future_change", "future_change_pct", "future_direction", "future_direction_num"], errors="ignore")
        y = df["future_direction_num"]

        X = X.select_dtypes(include=[np.number])
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)

        valid_idx = X.index.intersection(y.index)
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]

        if len(y.unique()) < 2:
            self.log.info("target class 부족")
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

    def get_feature_importance_shap(self, df):
    
        df = df.copy()

        X = df.drop(columns=["datetime", "target", "future_close", "return"], errors="ignore")
        y = df["target"]

        X = X.select_dtypes(include=[np.number])
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced"
        )

        model.fit(X, y)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # shap version 대응
        if isinstance(shap_values, list):
            shap_matrix = shap_values[1]
        else:
            shap_matrix = shap_values[:, :, 1]

        shap_df = pd.DataFrame(shap_matrix, columns=X.columns)

        result = pd.DataFrame({
            "feature": X.columns,
            "mean_shap": shap_df.mean()
        })

        up = result.sort_values("mean_shap", ascending=False).head(15)
        down = result.sort_values("mean_shap").head(15)

        return up, down

    def cut_by_days(self, df, target_date, days):
        start = target_date - datetime.timedelta(days=days)
        return df[df["datetime"] >= start].copy()
