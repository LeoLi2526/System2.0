import os
import json

from utils.debug.fallback_logger import fallback_logger
from utils.load_selector import load_prompt_template, load_config, call_llm_dashscope
from utils.audio_integration_manager import AudioIntegrationManager
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")
result_path = os.getenv("RESULT_PATH")
class ActionExtractorWorker:
    def __init__(self):
        self.prompt_template = load_prompt_template("action_extraction") # 从文件加载提示模板
        self.config = load_config(config_path) # 从文件加载配置
    def extract_actions(self, text_input: Optional[str] = None) -> List[Dict[str, Any]]:
        if text_input:
            # 如果有文本输入，直接构造格式化数据
            import time
            from datetime import datetime
            
            transcription_data = {
                "full_text": text_input,
                "request_maker": "User",
                "participants": ["User"],
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            # 否则从文件读取转录结果
            with open(result_path, 'r', encoding='utf-8') as f:
                raw_audio_data = json.load(f)
            transcription_data = AudioIntegrationManager().convert_to_system_format(raw_audio_data) 

        full_text = transcription_data.get("full_text", "")
        request_maker = transcription_data.get("request_maker", "")
        participants = transcription_data.get("participants", [])
        history_actions = None
        start_time = transcription_data.get("start_time", "")

        prompt = self.prompt_template.replace("{full_text}", full_text).replace("{request_maker}", request_maker).replace("{participants}", ", ".join(participants)).replace("{history_actions}", history_actions or "").replace("{start_time}", str(start_time) )
        
        fallback_logger.logger.info(f"Action Extraction Prompt Length: {len(prompt)}")
        fallback_logger.logger.info(f"Agent Information: {self.config['llm']['extraction_model']}")

        response = call_llm_dashscope(prompt, 'extraction_model').get("actions", [])
        
        # 强制生成系统级唯一ID，确保 ID 的唯一性和格式统一
        import uuid
        from datetime import datetime
        
        for i, action in enumerate(response):
            # 使用时间戳 + UUID 前8位 + 序号 组合生成唯一ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_suffix = str(uuid.uuid4())[:8]
            action['id'] = f"action_{timestamp}_{unique_suffix}_{i}"
            
        return response
'''from utils.audio_integration_manager import AudioIntegrationManager
result_path = os.getenv("RESULT_PATH")
with open(result_path, 'r', encoding='utf-8') as f:
    raw_audio_data = json.load(f)
transcription_data = AudioIntegrationManager().convert_to_system_format(raw_audio_data)
x = ActionExtractorWorker().extract_actions(transcription_data)
print(x)'''

