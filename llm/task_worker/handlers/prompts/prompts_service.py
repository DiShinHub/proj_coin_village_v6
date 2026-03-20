
from task_worker.tool.log_tool import LogTool
from task_worker.graph.builds.base.graph_builder import BaseBuilder
from task_worker.graph.builds.intent_matching.graph_builder import IntentMatchingBuilder
from task_worker.graph.builds.base.rules import BaseRules
from task_worker.exception.llm_exception import LlmException


class PromptsService():
    __logger = LogTool.get_logger(__qualname__)
    
    def __init__(self):
        self.base_graph = BaseBuilder().build_graph()
        self.im_graph = IntentMatchingBuilder().build_graph()
        
    def handle_prompts(self, task):
        """
        프롬프트 처리 워커

        Parameters
        ----------
        task : 테스크 데이터 (dict)
        """
        
        data = task.get("data")
        employee_seq = data.get("employee_seq")
        employee_email = data.get("employee_email")
        slack_text = data.get("slack_text")
        
        # gen input_message
        input_message = BaseRules.generate_input_message(slack_text, employee_seq, employee_email)
        
        # 의도 분류 
        result = self.im_graph.invoke({"input_message": input_message})
        if result.get('llm_node_response_dict_prev') == None or\
            result.get('llm_node_response_dict_prev').get("intent") == None:
            raise LlmException("im_graph fail, no llm_node_response_dict_prev")
        
        intent = result.get('llm_node_response_dict_prev').get("intent")
        
        # Agentic Ai 실행
        llm_response = None 
        if intent == "create":
            result = self.gcm_graph.invoke({"input_message": input_message})
            llm_response = f"일정이 생성되었습니다. 확인해 주세요. {result.get('llm_node_response_text_prev')}"
        
        else:
            result = self.base_graph.invoke({"input_message": input_message})
            llm_response = f"요청에 답변드립니다. {result.get('llm_node_response_text_prev')}"
        
        return llm_response