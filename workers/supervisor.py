
from utils.load_selector import load_config
from workers.action_extractor import ActionExtractorWorker
from workers.intelligent_classifier import IntelligentActionClassifier
from workers.route_execute import RouteExecuter
from typing import Optional, List, Dict, Any
import os, asyncio
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
    async def extract_actions(self, text_input: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.action_extractor.extract_actions(text_input)
    
    async def extract_and_classify(self, text_input: Optional[str] = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        执行动作提取和初步分类
        返回: (以ID为键的动作提取结果字典, 包含分类信息的完整结果列表)
        """
        action_extractor_list = await self.extract_actions(text_input)
        # 将列表转换为字典，以ID为键，方便后续查找
        action_extractor_results = {item['id']: item for item in action_extractor_list if 'id' in item}
        
        classified_results = []
        tasks = []

        # 遍历字典的值进行分类
        for action_extractor_result in action_extractor_results.values():
            tasks.append(self.intelligent_classifier.classify_actions(action_extractor_result))
        
        # 并发执行分类
        classifier_results = await asyncio.gather(*tasks)

        # 组合结果
        for action_extractor_result, classifier_result in zip(action_extractor_results.values(), classifier_results):
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

    async def execute_filtered_actions(self, filtered_classified_results: List[Dict[str, Any]], action_extractor_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行经过筛选的动作列表
        :param filtered_classified_results: 经过筛选的分类结果列表
        :param action_extractor_results: 原始动作提取结果字典 (ID -> Action)
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
            
            for unknown_result in unknown_results:
                # 传入单个 unknown_result 包装成列表，以及完整的动作字典
                new_prompt, worker_type = prompt_creator.prompt_creation([unknown_result], action_extractor_results, user_advice=None)
                
                # 确保目录存在
                os.makedirs("utils/templates/prompt_templates/workers_templates/", exist_ok=True)
                
                temporary_prompt_path = f"utils/templates/prompt_templates/workers_templates/{worker_type}.txt"
                with open(temporary_prompt_path, "w", encoding="utf-8") as f:
                    f.write(new_prompt)
                
                worker_types.append({worker_type: unknown_result['id']})

        # 执行路由
        final_responses = await self.route_executer.execute(worker_types, action_extractor_results)
        return final_responses

    async def complete_process(self) -> List[Dict[str, Any]]:
        # 保留此方法以兼容旧调用方式，或作为全自动流程的入口
        action_extractor_results, classified_results = await self.extract_and_classify()
        return await self.execute_filtered_actions(classified_results, action_extractor_results)

if __name__ == "__main__":
    async def main():
        x = await SupervisorWorker().complete_process()
        print(x)
    asyncio.run(main())
