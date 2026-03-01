from modules.postgres import *

class runnableServicesDao():
    
    def __init__(self):
        self.postgres = Postgres()

    """
    runnable_service
    """
    def get_CvResearchProd02Gen01_runnable_service(self):

        query = f"""
            SELECT
                seq,
                execution_path,
                execution_class,
                execution_method,
                product_name,
                product_desc,
                reg_dt,
                reg_member_seq,
                mod_dt,
                mod_member_seq,
                activate_yn,
                service_options,
                interval_options,
                schedule_options
            FROM
                runnable_services
            WHERE execution_class = 'CvResearchProd02Gen01'
        """
        return self.postgres.read_one(query) 
    