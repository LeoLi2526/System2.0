import os
import json

from utils.debug.fallback_logger import fallback_logger
from utils.load_selector import load_prompt_template, load_config, call_llm_dashscope
from typing import Optional, List, Dict, Any
from dashscope import Generation
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("config_path")

class ActionExtractorWorker:
    def __init__(self):
        self.prompt_template = load_prompt_template("action_extraction") # 从文件加载提示模板
        self.api_key = os.getenv("DASHSCOPE_API_KEY") # 从环境变量加载API密钥
        self.config = load_config(config_path) # 从文件加载配置
        self.call_llm = call_llm_dashscope
    def extract_actions(self, transcription_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        

        full_text = transcription_data.get("full_text", "")
        event_maker = transcription_data.get("event_maker", "")
        participants = transcription_data.get("participants", [])
        history_actions = None
        start_time = transcription_data.get("start_time", "")

        prompt = self.prompt_template.replace("{full_text}", full_text).replace("{event_maker}", event_maker).replace("{participants}", ", ".join(participants)).replace("{history_actions}", history_actions or "").replace("{start_time}", str(start_time) )
        
        fallback_logger.logger.info(f"Action Extraction Prompt Length: {len(prompt)}")
        fallback_logger.logger.info(f"Agent Information: {self.config['llm']['extraction_model']}")

        response = self.call_llm(prompt, self.config['llm']['extraction_model'])


