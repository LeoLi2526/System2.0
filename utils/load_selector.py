from utils.debug.fallback_logger import fallback_logger
import yaml,os,re,json
from typing import Optional, List, Dict, Any
from dashscope import Generation
def load_prompt_template(template_name: str, for_worker: str = False) -> str:
    """
    从文件加载提示模板
    """
    try:
        if for_worker == False:
            with open(f"utils/templates/prompt_templates/{template_name}.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            with open(f"utils/templates/prompt_templates/workers_templates/{template_name}.txt", "r", encoding="utf-8") as f:
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
    
def call_llm_dashscope(prompt: str, model_name: str) -> Optional[str]:
    try:
        config_path = os.getenv("CONFIG_PATH")
        config = load_config(config_path)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        response = Generation.call(
            model=config['llm'][model_name],
            prompt=prompt,
            api_key=api_key,
            max_tokens=config['llm']['max_tokens'],
            temperature=config['llm']['temperature'],
            response_format={"type":"json_object"}
        )

        fallback_logger.logger.info(f"LLM Response Code: {response.status_code}")

        if response.status_code == 200:
                # 检查响应结构 - 从choices中获取内容
            result = response.output.choices[0].message.content
            cleaned_result = re.sub(r'^```json\s*', '', result, flags=re.MULTILINE)
            cleaned_result = re.sub(r'```\s*$', '', cleaned_result, flags=re.MULTILINE)
            cleaned_result = cleaned_result.strip()
            fallback_logger.logger.info(f"W-8 LLM 响应内容: {cleaned_result[:200] if cleaned_result else 'None'}...")
            result = json.loads(cleaned_result)
            return result
                
        else:
            fallback_logger.logger.error(f"W-8 LLM 调用失败，状态码: {response.status_code}, 错误: {response}")
            return None
                
    except Exception as e:
        fallback_logger.logger.error(f"W-8 LLM 调用异常: {str(e)}", exc_info=True)
        return None


def load_worker_capabilities() -> Dict[str, Any]:
    """加载Worker能力定义"""
    capabilities_path = os.getenv("CAPABILITIES_PATH")
    try:
        with open(capabilities_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        fallback_logger.logger.error(f"加载Worker能力定义失败: {e}")