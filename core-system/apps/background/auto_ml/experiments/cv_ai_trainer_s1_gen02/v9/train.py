

class Train():
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
        return self.train() # returns will be sent to metric (DO not fix return)
    
    """
    fixable
    """
    def train(self):
        # train with df
        return