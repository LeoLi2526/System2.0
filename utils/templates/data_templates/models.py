from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Action(BaseModel):
    mission_id: str #需求ID
    action_type: str #动作类型
    descriptions: Dict[str, Any] #需求描述
    location_lat: Optional[float] = None #位置信息纬度
    location_lng: Optional[float] = None #位置信息经度
    confidence: Optional[float] = None #置信度
