
from utils.load_selector import load_config
from workers.action_extractor import ActionExtractorWorker
from workers.intelligent_classifier import IntelligentActionClassifier
from workers.route_execute import RouteExecuter
from typing import Optional, List, Dict, Any
import os
from workers.prompt_creator import PromptCreatorWorker
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")

class SupervisorWorker:
    def __init__(self):
        self.config = load_config(config_path) # 从文件加载配置

        #Worker Initialization
        self.action_extractor = ActionExtractorWorker()
        self.intelligent_classifier = IntelligentActionClassifier()
        self.route_executer = RouteExecuter()

    #Action Extraction
    def extract_actions(self) -> List[Dict[str, Any]]:
        return self.action_extractor.extract_actions()
    #....................................add more workers........................#
    #....................................add more workers........................#

      
    def complete_process(self) -> List[Dict[str, Any]]:
        classifier_results = []
        unknown_results = []
        worker_types = []
        action_extractor_results = self.extract_actions()

        for action_extractor_result in action_extractor_results:
            classifier_result = self.intelligent_classifier.classify_actions(action_extractor_result)
            plus_information = {
                "id": action_extractor_result.get("id", ""),
                "request_maker": action_extractor_result.get("request_maker", []),
                "start_time": action_extractor_result.get("start_time", "")               
            }

            classifier_full_result = {**plus_information, **classifier_result}

            if classifier_full_result.get("worker_type") == "unknown":
                unknown_results.append(classifier_full_result)
            else:
                classifier_results.append(classifier_full_result)

        for classifier_result in classifier_results:
            worker_types.append({classifier_result['worker_type']:classifier_result['id']})

        #classifier_results+unknown_results是完整的分类器输出列表
        if len(unknown_results) > 0:
            for unknown_result in unknown_results:
                prompt_creator = PromptCreatorWorker()
                new_prompt , worker_type = prompt_creator.prompt_creation([unknown_result], action_extractor_results,user_advice = None)   
                temporary_prompt_path = "utils/templates/prompt_templates/workers_templates/"+f"{worker_type}.txt"
                with open(temporary_prompt_path, "w", encoding="utf-8") as f:
                    f.write(new_prompt)             
                worker_types.append({worker_type:unknown_result['id']})

        
        final_responses = self.route_executer.execute(worker_types, action_extractor_results)

        return final_responses

        
        





x = SupervisorWorker().complete_process()
print(x)
