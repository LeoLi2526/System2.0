import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class AudioIntegrationManager:
    def __init__(self, result_path: str = "./process_results/transcription_result.json"):
        self.result_path = Path(result_path)
        self.last_processed_time = None
    
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
        request_maker = segments[0]["speaker"] 
        start_time = metadata.get("start_time", "")

        return {
            "transcription": combined_text,
            "segments": segments,
            "full_text": full_text,
            "metadata": audio_data.get("meta", {}),
            "source": "audio_agent",
            "request_maker": request_maker,
            "participants": participants,
            "start_time": start_time
        }