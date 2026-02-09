import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class AudioIntegrationManager:
    def __init__(self, result_path: str = "./process_results/transcription_result.json"):
        self.result_path = Path(result_path)
        self.last_processed_time = None
        
    async def wait_for_new_transcription(self, timeout: int = 120) -> dict:
        """等待新的转录结果"""
        start_time = datetime.now()
        
        print(f"🔄 等待音频转录结果... (超时: {timeout}秒)")
        print(f"💡 请在另一个终端运行: python agents/audio_agent.py")
        print(f"💡 开始录音后，系统将自动处理转录结果")
        
        while (datetime.now() - start_time).seconds < timeout:
            if self.result_path.exists():
                try:
                    stat = self.result_path.stat()
                    file_modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    # 如果文件被更新且不是上次处理的
                    if (self.last_processed_time is None or 
                        file_modified > self.last_processed_time):
                        
                        try:
                            with open(self.result_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            print(f"✅ 检测到新的音频转录结果!")
                            self.last_processed_time = file_modified
                            return data
                            
                        except json.JSONDecodeError:
                            # 文件可能正在写入，稍等重试
                            await asyncio.sleep(0.5)
                            continue
                        except Exception as e:
                            print(f"❌ 读取转录文件错误: {e}")
                            await asyncio.sleep(0.5)
                            continue
                except OSError:
                    # 文件可能暂时不可访问
                    await asyncio.sleep(0.5)
                    continue
            
            await asyncio.sleep(0.5)  # 短暂休眠避免CPU占用过高
            
        raise TimeoutError("等待音频转录超时")
    
    def convert_to_system_format(self, audio_data: dict) -> dict:
        """将音频代理输出转换为系统格式"""
        # 获取最新转录
        content = audio_data.get("content", [])
        full_text = audio_data.get("full_text", "")
        metadata = audio_data.get("meta", {})
        # 提取所有文本片段
        text_parts = []
        segments = []
        participants = []
        for item in content:
            if "text" in item and item["text"].strip():
                text_parts.append(item["text"])
                segments.append({
                    "text": item["text"],
                    "timestamp": item.get("time", item.get("timestamp", "")),
                    "speaker": item.get("speaker", "Speaker"),
                    "is_final": item.get("status", "final") == "final"
                })
        
        combined_text = "".join(full_text) if full_text else text_parts
        for item in segments:
            if item["speaker"] not in participants:
                participants.append(item["speaker"])
        event_maker = segments[0]["speaker"] if segments else "Speaker"
        start_time = metadata.get("start_time", "")

        return {
            "transcription": combined_text,
            "segments": segments,
            "full_text": full_text,
            "metadata": audio_data.get("meta", {}),
            "source": "audio_agent",
            "event_maker": event_maker,
            "participants": participants,
            "start_time": start_time
        }