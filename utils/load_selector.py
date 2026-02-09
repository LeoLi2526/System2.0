from utils.debug.fallback_logger import fallback_logger
import yaml
from typing import Optional, List, Dict, Any
from dashscope import Generation
def load_prompt_template(template_name: str) -> str:
    """
    从文件加载提示模板
    """
    try:
        with open(f"utils/templates/prompt_templates/{template_name}.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        fallback_logger.log_error("prompt_selector", f"提示模板 加载失败:{str(e)}")
        return ""
    
def load_config(config_path: str) -> Dict[str, Any]:
    """
    从文件加载配置
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        fallback_logger.log_error("config_loader", f"配置文件 加载失败:{str(e)}")
        return {}
    
async def call_llm_dashscope(self, prompt: str, model_name: str) -> Optional[str]:
    try:
        response = Generation.call(
            model=self.config['llm'][model_name],
            prompt=prompt,
            api_key=self.api_key,
            max_tokens=self.config['llm']['max_tokens'],
            temperature=self.config['llm']['temperature'],
            result_format={"type":"json_object"}
        )

        fallback_logger.logger.info(f"LLM Response Code: {response.status_code}")

        if response.status_code == 200:
                # 检查响应结构 - 从choices中获取内容
            if hasattr(response, 'output') and response.output:
                    # 优先检查choices数组
                if 'choices' in response.output:
                    choices = response.output.get('choices', [])
                    if choices:
                        first_choice = choices[0]
                        if isinstance(first_choice, dict) and 'message' in first_choice:
                            message = first_choice['message']
                            if isinstance(message, dict) and 'content' in message:
                                result = message['content']
                                if content:
                                    fallback_logger.logger.info(f"W-8 LLM 响应内容: {content[:200] if content else 'None'}...")
                                    return result
                    
                    # 如果没有choices，尝试直接获取text
                result = response.output.get("text", "")
                if result:
                    fallback_logger.logger.info(f"W-8 LLM 响应内容: {content[:200] if content else 'None'}...")
                    return result
                        
                # 如果output不存在或为空，检查整个response是否有text字段
            if hasattr(response, 'text'):
                content = response.text
                fallback_logger.logger.info(f"W-8 LLM 响应内容: {content[:200] if content else 'None'}...")
                return content
                    
                # 如果text也为空，记录错误
            fallback_logger.logger.error(f"W-8 LLM 输出内容为空: {response.output}")
            return None
        else:
            fallback_logger.logger.error(f"W-8 LLM 调用失败，状态码: {response.status_code}, 错误: {response}")
            return None
                
    except Exception as e:
        fallback_logger.logger.error(f"W-8 LLM 调用异常: {str(e)}", exc_info=True)
        return None
