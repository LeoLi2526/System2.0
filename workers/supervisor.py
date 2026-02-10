
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
    
    def extract_and_classify(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        执行动作提取和初步分类
        返回: (所有动作提取结果列表, 包含分类信息的完整结果列表)
        """
        action_extractor_results = self.extract_actions()
        classified_results = []

        for action_extractor_result in action_extractor_results:
            classifier_result = self.intelligent_classifier.classify_actions(action_extractor_result)
            # 组合基本信息和分类结果
            plus_information = {
                "id": action_extractor_result.get("id", ""),
                "request_maker": action_extractor_result.get("request_maker", []),
                "start_time": action_extractor_result.get("start_time", ""),
                # 保留原始描述以便查看
                "original_description": action_extractor_result.get("descriptions", {}) 
            }
            
            classifier_full_result = {**plus_information, **classifier_result}
            classified_results.append(classifier_full_result)
            
        return action_extractor_results, classified_results

    def execute_filtered_actions(self, filtered_classified_results: List[Dict[str, Any]], action_extractor_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行经过筛选的动作列表
        """
        worker_types = []
        unknown_results = []
        
        # 分离已知和未知类型的任务
        for result in filtered_classified_results:
            if result.get("worker_type") == "unknown":
                unknown_results.append(result)
            else:
                worker_types.append({result['worker_type']: result['id']})

        # 处理未知类型的任务 (Prompt Creation)
        if len(unknown_results) > 0:
            prompt_creator = PromptCreatorWorker()
            # 这里简化处理，虽然 prompt_creation 看起来能处理多个，但根据代码逻辑它似乎一次生成一个类型的prompt? 
            # 原代码逻辑：prompt_creator.prompt_creation 接受列表，似乎是针对一组unknown的任务生成一个prompt?
            # 让我们仔细看看原代码：
            # new_prompt , worker_type = prompt_creator.prompt_creation([unknown_result], action_extractor_results, user_advice = None)
            # 它是在循环里调用的，所以是对每个unknown结果单独处理。
            
            for unknown_result in unknown_results:
                # 注意：prompt_creator.prompt_creation 需要传入 problem_results 列表和 action_extractor_results
                # 这里我们传入单个 unknown_result 包装成列表
                new_prompt, worker_type = prompt_creator.prompt_creation([unknown_result], action_extractor_results, user_advice=None)
                
                # 确保目录存在
                os.makedirs("utils/templates/prompt_templates/workers_templates/", exist_ok=True)
                
                temporary_prompt_path = f"utils/templates/prompt_templates/workers_templates/{worker_type}.txt"
                with open(temporary_prompt_path, "w", encoding="utf-8") as f:
                    f.write(new_prompt)
                
                worker_types.append({worker_type: unknown_result['id']})

        # 执行路由
        final_responses = self.route_executer.execute(worker_types, action_extractor_results)
        return final_responses

    def complete_process(self) -> List[Dict[str, Any]]:
        # 保留此方法以兼容旧调用方式，或作为全自动流程的入口
        action_extractor_results, classified_results = self.extract_and_classify()
        return self.execute_filtered_actions(classified_results, action_extractor_results)

if __name__ == "__main__":
    x = SupervisorWorker().complete_process()
    print(x)
