import os
import json
import time
import asyncio
from datetime import datetime
from workers.supervisor import SupervisorWorker

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def save_text_input():
    print("=== 文本输入模式 ===")
    print("请输入文本内容（输入 END 结束）：")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    text_content = "".join(lines)
    
    if not text_content.strip():
        print("内容为空，未保存。")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"text_input_{timestamp}.txt"
    save_dir = "process_results"
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    file_path = os.path.join(save_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)
        
    print(f"文本已保存至: {file_path}")
    print("正在初始化系统并处理文本输入...")
    asyncio.run(process_interaction(text_input=text_content))

def handle_voice_input():
    print("=== 语音输入模式 ===")
    print("请按照以下步骤操作：")
    print("1. 请在另一个终端窗口中运行音频代理程序：python agents/audio_agent.py")
    print("2. 在音频代理完成录音和转录后，确保结果已保存。")
    input("3. 确认完成后，请在此处按回车键继续...")
    
    print("正在初始化系统并读取语音转录...")
    asyncio.run(process_interaction())

async def process_interaction(text_input=None):
    """
    统一处理用户交互流程
    :param text_input: 如果有值，则为文本输入模式；否则为语音输入模式
    """
    try:
        supervisor = SupervisorWorker()
        # 获取原始动作数据和分类结果
        action_results, classified_results = await supervisor.extract_and_classify(text_input=text_input)
        
        if not classified_results:
            print("未提取到任何有效的动作或意图。")
            input("按回车键返回主菜单...")
            return

        

        print(f"成功提取到 {len(classified_results)} 个潜在动作。")
        print("-" * 50)
        
        filtered_results = []
        
        for i, result in enumerate(classified_results):
            print(f"动作 #{i+1} [ID: {result.get('id', 'N/A')}]")
            
            # 显示详细信息以便用户判断
            original_desc = result.get('original_description', {})
            details = original_desc.get('details', '无详细描述')
            
            print(f"详情: {details}")
            print(f"分类意图: {result.get('worker_type', 'Unknown')}")
            print(f"置信度: {result.get('confidence', 0)}")
            print(f"分类理由: {result.get('reason', '无')}")
            
            while True:
                choice = input("是否执行此动作？(y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    filtered_results.append({"id":id,"result":result})
                    print("已加入执行队列。")
                    break
                elif choice in ['n', 'no']:
                    print("已忽略此动作。")
                    break
                else:
                    print("请输入 y 或 n。")
            print("-" * 50)
            
        if not filtered_results:
            print("没有待执行的动作。")
        else:
            print(f"开始执行筛选后的 {len(filtered_results)} 个动作...")

            enhanced_records = await supervisor.create_enhanced_records(filtered_results, action_results)
            filtered_results = [item["result"] for item in filtered_results]
            final_responses = await supervisor.execute_filtered_actions(filtered_results, action_results)
            
            print("=== 执行结果 ===")
            print(json.dumps(final_responses, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("按回车键返回主菜单...")

def main():
    while True:
        clear_screen()
        print("=== System 2.0 智能助手系统 ===")
        print("1. 语音输入模式")
        print("2. 文本输入模式")
        print("3. 退出系统")
        print("===============================")
        
        choice = input("请输入选项 (1-3): ").strip()
        
        if choice == '1':
            handle_voice_input()
        elif choice == '2':
            save_text_input()
        elif choice == '3':
            print("感谢使用，再见！")
            break
        else:
            input("无效选项，请按回车键重试...")

if __name__ == "__main__":
    main()
