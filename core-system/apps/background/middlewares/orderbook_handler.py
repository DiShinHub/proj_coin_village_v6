from background.modules.redis import r as redis_single

class OrderbookHandler():
    """
    description : 호가 데이터 핸들러
    
    - orderbook_key를 통해 큐 선택할 수 있음
    - 지정 된 큐에서 호가 조회회
    - 신규 호가만 사용 
    - 코어 실행은 오버라이딩하여 재정의 필요
    """
    
    def __init__(self, orderbook_key=None, **kwargs):
        self.redis = redis_single
        
        # system attrs
        self.orderbook_key = orderbook_key
        self.timestamp_lasts = {}
        
    def monitoring_order_books(self):
        
        while True:
            try:
                # 호가 데이터 조회
                order_book_keys = self.get_order_books_from_queue()
                if order_book_keys:
                    for order_book_key in order_book_keys:
                        
                        # key 파싱
                        order_book_parsed = order_book_key.split("_")
                        ticker = order_book_parsed[1]
                        timestamps_order_book = float(order_book_parsed[2])
                        
                        # 신규 호가만 사용 
                        if self.timestamp_lasts.get(ticker):
                            if timestamps_order_book > self.timestamp_lasts.get(ticker):
                                self.execute_core_process(ticker, order_book_key)
                        
                        # 티커별 마지막 타임스탬프 기재
                        self.timestamp_lasts[ticker] = timestamps_order_book
                     
            except Exception as e:   
                raise e
                
    def get_order_books_from_queue(self):
        """
        def description : 큐에서 호가 n개 조회 후 시간순으로 정렬
        """
        
        keys = self.redis.get_keys(f"{self.orderbook_key}", 100)
        sorted_keys = sorted(keys, key=lambda x: float(x.rsplit('_', 1)[-1]))
        
        return sorted_keys
    
    def execute_core_process(self):
        """
        def description : 코어 프로세스 실행 (Abstract Method)
        """
        pass