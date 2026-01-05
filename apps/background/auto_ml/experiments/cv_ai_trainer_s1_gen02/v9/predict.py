

class Predict():
    """
    DO NOT FIX 
    - Class's Name
    - Method, __init__
    - Method, main's name & return type
    
    those method will be called by middleware of auto ml 
    """
    def __init__(self, df):
        self.df = df
    
    def main(self):
        # write your code
        return self.predict() 
    
    """
    fixable
    """
    def predict(self, model, df):
        # predict with model, df
        return