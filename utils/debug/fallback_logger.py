import logging
from datetime import datetime
from pathlib import Path
import json

class FallbackLogger:

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.fallback_logger_path = self.log_dir / f"fallback_log_{datetime.now().strftime('%Y%m%d')}.log"

        self.logger = logging.getLogger("fallback")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(self.fallback_logger_path, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_fallback(self, source: str, reason: str, confidence: float, fallback_data: dict = None):
        """
        记录降级事件
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "reason": reason,
            "confidence": confidence,
            "fallback_data": fallback_data or {}
        }
        
        # 写入日志文件
        self.logger.info(json.dumps(event, ensure_ascii=False))
        
        # 可选：如果集成 Langfuse，在此处添加埋点
        # from langfuse import Langfuse
        # langfuse = Langfuse()
        # trace = langfuse.trace(name=f"fallback_{source}")
        # trace.event(name="fallback_occurred", metadata=event)
    
    def log_error(self, source: str, error_msg: str):
        """
        记录严重错误（导致流程中断）
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "error": error_msg
        }
        
        self.logger.error(json.dumps(event, ensure_ascii=False))


# 全局日志实例
fallback_logger = FallbackLogger()
