from datetime import datetime
from typing import List
from uuid import UUID
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import uuid            

@dataclass_json
@dataclass
class DTO_Metric:
    name: str
    value: float

@dataclass_json
@dataclass
class DTO_Snapshot:
    timestamp_capture: datetime = field(default_factory=datetime.now)
    timezone_mins: int = 0
    metrics: List[DTO_Metric] = field(default_factory=list)
 
@dataclass_json
@dataclass 
class DTO_Device:
    name: str
    snapshots: List[DTO_Snapshot] = field(default_factory=list)
    
@dataclass_json
@dataclass
class DTO_Aggregator:
    guid: uuid
    name: str
    devices: List[DTO_Device] = field(default_factory=list)

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'name': self.name,
            'devices': [device.to_dict() for device in self.devices]
        }