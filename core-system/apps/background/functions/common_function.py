import datetime
from datetime import  timedelta
import time


import ast
import json

import importlib.util
import os
import inspect

def generate_now_date():
    """ 
    def description : 오늘 날짜 연월일 시분초 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 연월일 시분초
    """
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now_date

def generate_now_date_til_min():
    """ 
    def description : 오늘 날짜 연월일 시분초 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 연월일 시분초
    """
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return now_date

def generate_n_date_after(n):
    """ 
    def description : n일 후 연월일 시분초 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        n일 후 연월일 시분초 산출
    """
    n_date_after = (datetime.datetime.now() + datetime.timedelta(days=n)).strftime("%Y-%m-%d %H:%M:%S")
    return n_date_after

def generate_n_min_after(n):
    """ 
    def description : n분 후 연월일 시분초 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        n분 후 연월일 시분초 산출
    """
    n_date_after = (datetime.datetime.now() + datetime.timedelta(minutes=n)).strftime("%Y-%m-%d %H:%M:%S")
    return n_date_after

def generate_now_year():
    """ 
    def description : 오늘 날짜 연 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 연
    """
    now_day = datetime.datetime.now().strftime("%Y")
    return now_day

def generate_now_day():
    """ 
    def description : 오늘 날짜 연월일 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 연월일
    """
    now_day = datetime.datetime.now().strftime("%Y-%m-%d")
    return now_day

def generate_now_time():
    """ 
    def description : 오늘 날짜 시분초 산출

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 시분초
    """
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    return now_time


def generate_now_min():
    """ 
    def description : 현재 분 산출

    Returns
    -------
    mm 분
    """
    mm = generate_now_time()[-5:-3]
    return int(mm)


def generate_now_sec():
    """ 
    def description : 현재 초 산출

    Returns
    -------
    ss 초
    """
    ss = generate_now_time()[-2:]
    return int(ss)


def generate_micro_date():
    """ 
    def description : 오늘 날짜 마이크로 세컨드까지 산출 

    Parameters
    ----------
    없음 

    Returns
    -------
    datetime
        오늘 날짜 마이크로 세컨드
    """
    now_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")

    return now_date

def generate_datetimes_by_min(terms, interval, start_date=None, n_days_ago=None, fmt="%Y-%m-%d %H:%M:%S"):
    
    datetime_ = datetime.datetime.now()
    if start_date: datetime_ = start_date
    if n_days_ago: datetime_ = datetime_ - datetime.timedelta(days=7)
    
    # interval 기준으로 내림 + 초, 마이크로초 제거
    minute_adjusted = (datetime_.minute // interval) * interval
    aligned_now = datetime_.replace(minute=minute_adjusted, second=0, microsecond=0)
    
    # 한 interval 더 빼기
    aligned_now -= timedelta(minutes=interval)

    start_time = aligned_now - timedelta(days=terms)
    delta = timedelta(minutes=interval)

    total_minutes = (aligned_now - start_time).total_seconds() // 60
    steps = int(total_minutes // interval) + 1

    return [
        (start_time + i * delta).replace(second=0, microsecond=0).strftime(fmt)
        for i in range(steps)
    ]
    
def get_years_between_str(start_str: str, end_str: str, fmt="%Y-%m-%d %H:%M:%S"):
    
    start = datetime.datetime.strptime(start_str, fmt)
    end = datetime.datetime.strptime(end_str, fmt)
    
    return list(range(start.year, end.year + 1))


def split_date_range_by_year(start_str, end_str):
    start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
    
    result = {}
    for year in range(start_dt.year, end_dt.year + 1):
        year_start = datetime.datetime(year, 1, 1)
        year_end = datetime.datetime(year, 12, 31, 23, 59, 59)
        
        range_start = max(start_dt, year_start)
        range_end = min(end_dt, year_end)
        
        result[year] = (range_start.strftime("%Y-%m-%d %H:%M:%S"), range_end.strftime("%Y-%m-%d %H:%M:%S"))
    
    return result

def cal_time_changes(flag_time):
    """ 
    def description : 시간변화 체크

    Parameters
    ----------
    start_time : 시작 시간 

    Returns
    -------
    float : 시작 시간으로부터 현재 시간 차이 (sec)
    """

    now_time = time.time()
    time_diff = (now_time - flag_time)
    return time_diff


def cal_price_changes(f_close, l_close):
    """ 
    def description : 가격 변화 산출 

    Parameters
    ----------
    f_close : 시가
    l_close : 종가

    Returns
    -------
    change_rate : 변화율
    """
    change_rate = round(((l_close - f_close) / f_close) * 100, 3)
    return change_rate

def cal_weekday_code(date_string):
    """ 
    def description : 요일 산출

    Parameters
    ----------
    date_string : 날짜 (yyyy-mm-dd)

    Returns
    -------
    change_rate : 요일
    """
    # 날짜를 입력
    date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")

    # 요일 출력 (0: 월요일, 6: 일요일)
    weekdays = ["0", "1", "2", "3", "4", "5", "6"]
    weekday = weekdays[date_object.weekday()]
    return weekday


def floor_to_5m(dt):
    return dt.replace(minute=(dt.minute // 5) * 5, second=0, microsecond=0)

def get_5m_ticks_exact(last_dt_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    
    now_dt = datetime.strptime(generate_now_date(), fmt)
    last_dt = datetime.strptime(last_dt_str, fmt)
    
    now_5m = floor_to_5m(now_dt)
    last_5m = floor_to_5m(last_dt)
    
    delta = now_5m - last_5m
    ticks = int(delta.total_seconds() / 300)  # 300초 = 5분
    
    return ticks

def generate_weekday_kor():
    """ 
    def description : 요일 산출

    Returns
    -------
    change_rate : 요일
    """
    # 현재 시간 구하기
    now = datetime.datetime.now()

    # 요일 번호 (0:월, 1:화, ..., 6:일)
    weekday_index = now.weekday()

    # 한글 요일 리스트 (월 ~ 일)
    kor_weekdays = ['월', '화', '수', '목', '금', '토', '일']
    kor_weekday = kor_weekdays[weekday_index]
    return kor_weekday

def sort_by_current_price(data_list):
    """ 
    def description : 현재가 기준으로 정렬 

    Parameters
    ----------
    data_list : 데이터 리스트 (list)

    Returns
    -------
    data_list : 데이터 리스트 (list)
    """
    arr = data_list
    for i in range(len(arr) - 1, 0, -1):
        for j in range(i):
            if arr[j]["current_price"] < arr[j + 1]["current_price"]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

    return data_list


def add_sec(target_time, sec):
    """ def description : 타겟 시간에 초 추가

    Parameters : 
    target_time : 타겟 시간 (str, 23:59:59)
    sec : 추가할 초(int)

    Returns
    -------
    Boolean
    """
    if abs(int(sec)) >= 60:
        return False

    hh = int(target_time[0:2])
    mm = int(target_time[3:5])
    ss = int(target_time[6:8])

    ss += sec
    if sec > 0:

        if ss >= 60:
            ss = ss - 60
            mm += 1

        if mm >= 60:
            mm = mm - 60
            hh += 1

        if hh >= 24:
            hh = hh - 24

    else:

        if ss < 0:
            ss = abs(ss + 60)
            mm += -1

        if mm < 0:
            mm = abs(mm + 60)
            hh += -1

        if hh < 0:
            hh = abs(hh + 24)

    hh = str(hh).zfill(2)
    mm = str(mm).zfill(2)
    ss = str(ss).zfill(2)

    result_time = f"{hh}:{mm}:{ss}"
    return result_time


def add_min(target_time, min):

    if abs(int(min)) >= 60:
        return False

    hh = int(target_time[0:2])
    mm = int(target_time[3:5])
    ss = int(target_time[6:8])

    mm += min
    if mm > 0:

        if mm >= 60:
            mm = mm - 60
            hh += 1

        if hh >= 24:
            hh = hh - 24

    else:

        if mm < 0:
            mm = abs(mm + 60)
            hh += -1

        if hh < 0:
            hh = abs(hh + 24)

    hh = str(hh).zfill(2)
    mm = str(mm).zfill(2)
    ss = str(ss).zfill(2)

    result_time = f"{hh}:{mm}:{ss}"
    return result_time

def find_target_dictionary(key, val, dictionaries):
    """ 
    def description : dictionaries에서 key/val에 해당하는 dictionary 리턴

    Parameters
    ----------
    key : 찾고자 하는 데이터 키
    val : 찾고자 하는 데이터 값
    dictionaries : 대상 딕셔너리 리스트 (list(dict))

    Returns
    -------
    data : 변환 된 데이터
    """
    
    for dictionary in dictionaries:
        if dictionary[key] == val: # HIT
            return dictionary

def parse_and_convert_string(data: str):
    """ 
    def description : 문자열 데이터를 dict, list, bytes... 중 적절한 형태로 변환

    Parameters
    ----------
    data : 원본 데이터

    Returns
    -------
    data : 변환 된 데이터
    """
    
    data = data.strip()

    # 1. bytes 형식 판별 (b'...' 또는 b"..." 형식)
    if (data.startswith("b'") or data.startswith('b"')) and data.endswith("'") or data.endswith('"'):
        try:
            return ast.literal_eval(data) 
        
        except (SyntaxError, ValueError):
            pass  

    # 2. JSON 형식 판별 (list 또는 dict)
    try:
        parsed = json.loads(data)
        if isinstance(parsed, (dict, list)):
            return parsed
        
    except json.JSONDecodeError:
        pass
    
    # 4. 변환 실패 시 원본 문자열 반환
    return data

def convert_eval_safe(val):
    try:
        # 문자열이지만 리터럴로 안전하게 파싱 가능한 경우만 변환
        return ast.literal_eval(val)
    
    except (ValueError, SyntaxError):
        return val  # 그냥 문자열로 둠

def convert_json_str_safe(val):
    try:
        # 문자열이지만 json으로 안전하게 파싱 가능한 경우만 변환
        return json.loads(val)
    
    except (ValueError, SyntaxError):
        return val  # 그냥 문자열로 둠

def map_interval_to_interval_min(interval):
    
    # interval_min을 interval을 통해 조회 
    if not interval:
        return None

    elif interval == "minute15":
        interval_min = 15
    elif interval == "minute30":
        interval_min = 30
    elif interval == "hour1":
        interval_min = 1*60
    elif interval == "hour4":
        interval_min = 4*60
    elif interval == "hour12":
        interval_min = 12*60
    elif interval == "day":
        interval_min = 24*60
    
    return interval_min

def load_class_from_file(file_path: str, class_name: str):
    
    # 파일 이름에서 모듈 이름 생성 (확장자 제외)
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    # 모듈 스펙 로드
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Cannot find spec for {file_path}")
    
    # 모듈 객체 생성 및 실행
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore

    # 클래스 가져오기
    cls = getattr(module, class_name, None)
    if cls is None:
        raise AttributeError(f"Class '{class_name}' not found in {file_path}")
    
    return cls

def run_from_method_name(obj, method_name):
    method = getattr(obj, method_name)
    result = method()
    return result
