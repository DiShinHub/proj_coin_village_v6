from background.middlewares.service_process_handler import ProcessHandler

class BackgroundMain(ProcessHandler):
    
    def __init__(self):
        super().__init__()

    def run(self):
        super().run_handler()
            
if __name__ == "__main__":
    
    background_main = BackgroundMain()
    background_main.run()