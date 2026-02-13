
from utils.load_selector import load_config
from workers.action_extractor import ActionExtractorWorker
from workers.intelligent_classifier import IntelligentActionClassifier
from workers.route_execute import RouteExecuter
from typing import Optional, List, Dict, Any
import os, asyncio, json
from datetime import datetime
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

        # Data Saving Initialization
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join("data", f"run_{self.timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)

    def _save_data(self, filename: str, data: Any):
        """Helper to save data to the session directory"""
        try:
            filepath = os.path.join(self.session_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"数据已保存至: {filepath}")
        except Exception as e:
            print(f"保存数据失败 {filename}: {str(e)}")

    #Action Extraction
    async def extract_actions(self, text_input: Optional[str] = None) -> List[Dict[str, Any]]:
        actions, input_data = await self.action_extractor.extract_actions(text_input)
        self._save_data("action_extractor_input.json", input_data)
        return actions
    
    async def extract_and_classify(self, text_input: Optional[str] = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        执行动作提取和初步分类
        返回: (以ID为键的动作提取结果字典, 包含分类信息的完整结果列表)
        """
        action_extractor_list = await self.extract_actions(text_input)
        
        # 保存动作提取原始数据
        self._save_data("action_extractor_output.json", action_extractor_list)

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
        
        # 保存分类结果
        self._save_data("intelligent_classifier_output.json", classified_results)
            
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
        
        # 保存 Worker 执行结果
        self._save_data("workers_execution_output.json", final_responses)
        
        return final_responses

    async def complete_process(self) -> List[Dict[str, Any]]:
        # 保留此方法以兼容旧调用方式，或作为全自动流程的入口
        action_extractor_results, classified_results = await self.extract_and_classify()
        return await self.execute_filtered_actions(classified_results, action_extractor_results)

    async def create_enhanced_records(self , filtered_results,action_results) -> List[Dict[str, Any]]:
        """
        创建增强记录
        :param text_input: 输入文本
        :return: 增强记录列表
        """
        action_extractor_results, classified_results = action_results, filtered_results
        enhanced_records = []
        for classified_result in classified_results:
            if classified_result.get("result")["worker_type"] != "unknown":
                action_id = classified_result.get("id", "")
                action_extractor_result = action_extractor_results.get(action_id, {})
                enhanced_record = {
                    "id": action_id,
                    "classified_result": {"worker_type":classified_result.get("worker_type", ""), 
                                        "reason":classified_result.get("reason", ""),
                                        "confidence":classified_result.get("confidence", 0.0)},
                    "extraction_result": action_extractor_result,
                }
                enhanced_records.append(enhanced_record)

        return enhanced_records

if __name__ == "__main__":
    async def main():
        x = await SupervisorWorker().complete_process()
        print(x)
    asyncio.run(main())
