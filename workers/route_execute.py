from utils.load_selector import load_config, load_prompt_template, call_llm_dashscope
from typing import Optional, List, Dict, Any
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()
config_path = os.getenv("CONFIG_PATH")


class RouteExecuter:
    def __init__(self):
        self.config = load_config(config_path)


    def execute(self, worker_types: List[Dict[str, List]], action_extractor_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        final_responses = []
        for worker_type_dict in worker_types:
            # worker_types 实际上是 [{worker_type: id}, ...] 这种结构
            worker_type_name = list(worker_type_dict.keys())[0]
            id = worker_type_dict[worker_type_name]
            last_response = None
            user_advice = None
            prompt_template = load_prompt_template(worker_type_name, for_worker=True)
            
            # 直接通过字典查找
            action_extractor_result = action_extractor_results.get(id)
            
            if not action_extractor_result:
                print(f"警告：未找到 ID 为 {id} 的动作详情，跳过执行。")
                continue
            prompt = prompt_template.format_map({"descriptions":action_extractor_result})
            print(f"正在执行任务 [{worker_type_name}] (ID: {id})...")
            
            response = call_llm_dashscope(prompt, "worker_model")

            
            while True:  
                print("" + "="*20 + " 执行结果 " + "="*20)
                if isinstance(response, (dict, list)):
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                else:
                    print(response)
                print("="*50)
                
                # 用户确认环节
                user_input = input("结果是否满意？(y/输入修改意见): ").strip()  
                if user_input.lower() in ['y', 'yes', '']:
                    final_responses.append({id:response})
                    print("结果已确认。")
                    break
                else:
                    user_advice = user_input
                    last_response = response
                    print("已收到修改意见，正在重新生成...")
           
                
                # 如果有修改意见，插入修正 Prompt 片段
                    if user_advice and last_response:
                        correction_part = f"【修正模式】\n上一次的输出结果："+"{"+"last_response"+"}\n用户的修改意见："+"{"+"user_advice"+"}\n请根据用户的修改意见，对上一次的输出结果进行修改和完善。"
                    
                    # 尝试插入到格式指令之前
                        anchor = "请严格按照以下JSON格式输出："
                        if anchor in prompt_template:
                        # 在锚点之前插入
                        # split一次以防多个锚点（虽然不太可能）
                            parts = prompt.split(anchor, 1)
                            correction_part = correction_part.format_map({"last_response":last_response, "user_advice":user_advice})
                            current_prompt = parts[0] + correction_part + "" + anchor + parts[1]
                        else:
                        # 未找到锚点，追加到末尾
                            current_prompt = prompt_template + "" + correction_part

                    try:
                        #cycle_prompt = current_prompt_template.format_map({"last_response":last_response, "user_advice":user_advice})
                        cycle_response = call_llm_dashscope(current_prompt, "worker_model")
                        response = cycle_response
                    except Exception as e:
                        print(f"Prompt 构造失败: {e}")
                        break

                
        return final_responses
                
