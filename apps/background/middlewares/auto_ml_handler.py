from background.modules.log import system_module_log
from background.functions.common_function import *
    
import mlflow
import inspect
import os 

class AutoMlHandler():
    
    def __init__(self, auto_ml_path, df=None):
        self.log = system_module_log
        
        self.auto_ml_path= auto_ml_path
        self.df = df
    
    def get_df(self):
        return self.df
    
    def set_df(self, df):
        self.df = df
        return self.df

    """
    auto ml, executable
    """
    def execute_train_by_auto_ml(self):

        try:
            mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))  
            mlflow.set_experiment(self.set_experiment_name())
            with mlflow.start_run():
                self.apply_dervied_params()
                self.apply_preprocess()
                self.train_model()
                self.metric_model()
                
                run = mlflow.active_run()
                return {
                    "experiment_id" : run.info.experiment_id,
                    "run_id" : run.info.run_id
                }

        except Exception as e:
            self.log.info(f"class : {self.__class__.__name__}, method : {inspect.currentframe().f_code.co_name}, error : {str(e)}")
    
    def execute_predict_by_auto_ml(self, model):
        self.apply_dervied_params()
        self.apply_preprocess()
        predictions = self.predict_model(model)
        return predictions
        
    """
    auto ml, each part
    """
    def apply_dervied_params(self):
        
        df = self.df.copy()
        derived_class = self.load_class_from_file(f"{self.auto_ml_path}/derived.py", f"Derived")
        derived_obj = derived_class(df)
        self.run_method_dynamic(obj=derived_obj, method_name=f"main")
        self.df = derived_obj.df
        return self.df
    
    def apply_preprocess(self):
        
        df = self.df.copy()
        preprocess_class = self.load_class_from_file(f"{self.auto_ml_path}/preprocess.py", f"PreProcess")
        preprocess_obj = preprocess_class(df)
        self.run_method_dynamic(obj=preprocess_obj, method_name=f"main")
        self.df = preprocess_obj.df
        return self.df
    
    def train_model(self):
        
        df = self.df.copy()
        train_class = self.load_class_from_file(f"{self.auto_ml_path}/train.py", f"Train")
        train_obj = train_class(df)
        return self.run_method_dynamic(obj=train_obj, method_name=f"main")
    
    def metric_model(self, train_result):
        
        df = self.df.copy()
        metric_class = self.load_class_from_file(f"{self.auto_ml_path}/metric.py", f"Metric")
        metric_obj = metric_class(df)
        return self.run_method_dynamic(obj=metric_obj, method_name=f"main", train_result=train_result)
    
    def predict_model(self, model):
        
        df = self.df.copy()
        predict_class = self.load_class_from_file(f"{self.auto_ml_path}/predict.py", f"Predict")
        predict_obj = predict_class(df)
        return self.run_method_dynamic(obj=predict_obj, method_name=f"main", df=self.df, model=model)
    
    """
    auto ml, helper
    """
    def set_experiment_name(self):
        
        auto_ml_path_splited = self.auto_ml_path.split("/")
        experiment_name = f"{auto_ml_path_splited[-2]}_{auto_ml_path_splited[-1]}"
        return experiment_name
    
    def load_class_from_file(self, file_path: str, class_name: str):
        
        # 파일 이름에서 모듈 이름 생성 (확장자 제외)
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # 모듈 스펙 로드
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            raise ImportError(f"Cannot find spec for {file_path}")
        
        # 모듈 객체 생성 및 실행
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  

        # 클래스 가져오기
        cls = getattr(module, class_name, None)
        if cls is None:
            raise AttributeError(f"Class '{class_name}' not found in {file_path}")
        
        return cls

    def run_method_dynamic(self, obj, method_name, **options):
        method = getattr(obj, method_name)
        result = method(**options)
        return result
        