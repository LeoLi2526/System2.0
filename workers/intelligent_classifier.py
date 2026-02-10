
import os, json
from utils.debug.fallback_logger import fallback_logger
from typing import Optional, List, Dict, Any
from utils.load_selector import load_config, load_prompt_template, load_worker_capabilities, call_llm_dashscope, call_llm_dashscope_async
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")


class IntelligentActionClassifier:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.config = load_config(config_path)
        self.prompt_template = load_prompt_template("classification_prompt")

    async def primary_ai_analysis(self, action_extractor_result:Dict[Any, Any]):
        try:           
            worker_capabilities = load_worker_capabilities()

            #构建分类器输入
            action = action_extractor_result.get("action", [])
            prompt = self.prompt_template.format_map({
                "worker_capabilities":worker_capabilities,
                "action_extractor_result":action})
            response = await call_llm_dashscope_async(prompt, 'classification_model')
            return response
        except Exception as e:
            fallback_logger.logger.error(f"智能分类异常: {str(e)}")
            return {"worker_type": "unknown", "confidence": 0.0, "reason": f"分类异常: {str(e)}"}
            
    async def classify_actions(self, action_extractor_results:Dict[Any, Any]):
        #..............可以新增其他分类逻辑.........................#
        return await self.primary_ai_analysis(action_extractor_results)
    

    

