from utils.load_selector import load_prompt_template, load_config, call_llm_dashscope
import os
from utils.load_selector import load_worker_capabilities
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")
result_path = os.getenv("RESULT_PATH")

class PromptCreatorWorker:
    def __init__(self):
        self.prompt_template = load_prompt_template("prompt_creator") # 从文件加载提示模板
        self.config = load_config(config_path) # 从文件加载配置

    def prompt_creation(self,  problem_results:List[Dict[str, Any]], action_extractor_results:Dict[str, Any], user_advice:str = None) -> str:
        problem_full_informations = []
        worker_capabilities = load_worker_capabilities()
        for result in problem_results:
            id = result.get("id")
            # 直接通过字典查找，不再遍历列表
            action_extractor_result = action_extractor_results.get(id)
            if action_extractor_result:
                problem_full_information = {"id":result.get("id"), 
                                           "start_time":result.get("start_time"),
                                           "request_maker":result.get("request_maker"),
                                           "reason":result.get("reason"),
                                           "details":action_extractor_result.get("descriptions", {}).get("details")}
                problem_full_informations.append(problem_full_information)
                    
            if user_advice:
                break
            else:        
                prompt = self.prompt_template.format_map({"full_description": problem_full_informations, 
                                                        "worker_capabilities": worker_capabilities,
                                                        "user_advice": user_advice})
                response = call_llm_dashscope(prompt, 'promptcreator_model')
                process_prompt = response.get("prompt")[0]
                identity = process_prompt.get("identity")
                input_data = "{{descriptions}}"
                text_output = {key:"" for key in process_prompt.get("json_method")}
                tips = response.get("tips")
                tips_text = ";\n".join(tips)
                final_prompt = f"角色定位：{identity}\n输入数据：{input_data}\n注意事项：\n{tips_text}\n请严格按照以下JSON格式输出：\n"+"{"+"{text_output}"+"}"
                worker_type = response.get("worker_type")
        return final_prompt , worker_type  #用于未定义worker的prompt      

    