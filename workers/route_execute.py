from utils.load_selector import load_config, load_prompt_template, call_llm_dashscope
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")


class RouteExecuter:
    def __init__(self):
        self.config = load_config(config_path)


    def execute(self, worker_types: List[Dict[str, List]], action_extractor_results: Dict[str, Any]) -> Optional[str]:
        final_responses = []
        for worker_type_dict in worker_types:
            # worker_types 实际上是 [{worker_type: id}, ...] 这种结构
            # 这里的命名有些混淆，worker_type_dict 就是其中一个字典项
            worker_type_name = list(worker_type_dict.keys())[0]
            id = worker_type_dict[worker_type_name]
            
            prompt_template = load_prompt_template(worker_type_name, for_worker=True)
            
            # 直接通过字典查找，不再遍历列表
            action_extractor_result = action_extractor_results.get(id)
            
            if action_extractor_result:
                prompt = prompt_template.format_map({"descriptions":action_extractor_result})
                response = call_llm_dashscope(prompt, "worker_model")
                final_responses.append({id:response})

        return final_responses
                
