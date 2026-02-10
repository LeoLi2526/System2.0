from utils.load_selector import load_config, load_prompt_template, call_llm_dashscope
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")


class RouteExecuter:
    def __init__(self):
        self.config = load_config(config_path)


    def execute(self, worker_types: List[Dict[str, List]], action_extractor_results: List[Dict[str, Any]]) -> Optional[str]:
        final_responses = []
        for worker_type in worker_types:
            information = worker_type
            worker_type = list(worker_type.keys())[0]
            prompt_template = load_prompt_template(worker_type, for_worker=True)
            id = information[worker_type]
            for action_extractor_result in action_extractor_results:
                if action_extractor_result['id'] == id:
                    prompt = prompt_template.format_map({"descriptions":action_extractor_result})
                    response = call_llm_dashscope(prompt, "worker_model")
                    final_responses.append({id:response})

        return final_responses
                
