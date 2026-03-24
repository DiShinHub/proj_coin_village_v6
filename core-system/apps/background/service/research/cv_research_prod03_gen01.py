from background.middlewares.service_handler import ServiceHandler
from background.modules.exchange_upbit import ExChangeUpbit
from background.modules.log import Log
from background.modules.redis import r as redis_single

from background.dao.research_result_dao import ResearchResultDao
from collections import defaultdict
import json
import numpy as np
import datetime
import os

class CvResearchProd03Gen01(ServiceHandler):
    """
    Service Name : CvResearchProd03Gen01
    Generation : 01 
    
    Desc : 
    - 박스캣
    """
    pref_slack_msg_box = ""

    def __init__(
            self, 
            seq=None, 
            service_options=None,
            interval_options=None,
            schedule_options=None
        ):
        ServiceHandler.__init__(self, schedule_options=schedule_options, interval_options=interval_options)

        self.log = Log(os.path.basename(__file__)).get_logger()
        self.seq = seq
        self.service_options = service_options
        
        self.redis = redis_single
        self.upbit = ExChangeUpbit()

        self.research_result_dao = ResearchResultDao()

        self.tickers = self.service_options.get("tickers")
        self.ticker = None
        
        self.target_days_list = [
            # 31,
            # 62,
            # 93,
            #186,
            365
        ]
    
    def main(self):

        try:
            for ticker in self.tickers:
                
                self.ticker = ticker
                self.upbit.set_ticker(self.ticker)
                self.decide_box_zone()

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, error : {str(e)}")
    
    def decide_box_zone(self, anchor_days="365", anchor_interval="day"):

        box_zone_total = {}
        for days in self.target_days_list:
            data = self.fetch_all_ohlcv(days)
            
            box_zone_interval = {}
            for interval, df in data.items():
            
                # 1. 데이터
                closes = df['close'].values
            
                # 2. 가격 구간화 (binning)
                bins = 50  # resolution
                hist, bin_edges = np.histogram(closes, bins=bins)
            
                # 3. 밀집 구간 찾기
                density = hist / hist.sum()
            
                # 상위 밀집 구간 선택
                threshold = np.percentile(density, 50)
            
                high_density_idx = np.where(density >= threshold)[0]
            
                if len(high_density_idx) == 0:
                    return None
            
                # 4. 연속된 구간 찾기 (cluster)
                clusters = []
                current_cluster = [high_density_idx[0]]
            
                for i in range(1, len(high_density_idx)):
                    if high_density_idx[i] == high_density_idx[i-1] + 1:
                        current_cluster.append(high_density_idx[i])
                    else:
                        clusters.append(current_cluster)
                        current_cluster = [high_density_idx[i]]
            
                clusters.append(current_cluster)
                
                result = []
                tolerance = (bin_edges[1] - bin_edges[0]) * 0.2
                for cluster in clusters:
                    regi_line = bin_edges[cluster]

                    for price in regi_line:
                        matched_df = df[np.abs(df['close'] - price) <= tolerance]
                        for idx, row in matched_df.iterrows():
                            result.append({
                                "regi_line": float(price),
                                "datetime": row['datetime'].strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                box_zone_interval[interval] = result
            box_zone_total[str(days)] = box_zone_interval
            
        grouped_result = self.group_box_zone(box_zone_total)

        result_json = grouped_result
        result_markerable = ""

        params = {}
        params["runnable_service_seq"] = self.seq
        params["type"] = "upbit-box"
        params["exchange"] = "upbit"
        params["ticker"] = self.ticker
        params["tags"] = ["upbit", "box"]
        params["result_markerable"] = result_markerable
        params["result_json"] = result_json
        params["result_txt"] = ""
        params["reg_member_seq"] = 0
        params["mod_member_seq"] = 0

        self.research_result_dao.insert_with_limit(params, 10000)
                                    
    def fetch_all_ohlcv(self, days=30):

        count = 200
        base_intervals = [
            "day"
            #, "week"
        ]
        data = {}
        for interval in base_intervals:
                
            end_dt = datetime.datetime.now()
            start_dt = end_dt - datetime.timedelta(days=days)
            
            df = self.upbit.set_ohlcvs(interval, days, count, start_dt, end_dt)
            data[interval] = df

        return data
           
    def group_box_zone(self, box_zone_total):
        grouped_result = {}

        for days, intervals in box_zone_total.items():
            grouped_result[days] = {}

            for interval, records in intervals.items():
                temp_dict = {}  # 그냥 dict 사용

                # regi_line별로 datetime을 모으기
                for rec in records:
                    rl = rec['regi_line']
                    dt = rec['datetime']

                    if rl not in temp_dict:
                        temp_dict[rl] = []
                    temp_dict[rl].append(dt)

                # count 포함해서 최종 리스트 생성
                grouped_list = []
                for regi_line, datetimes in temp_dict.items():
                    grouped_list.append({
                        "regi_line": regi_line,
                        "datetimes": datetimes,
                        "count": len(datetimes)
                    })

                grouped_result[days][interval] = grouped_list
    
        return grouped_result