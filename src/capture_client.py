import time
from src.dto_datamodel import DTO_Aggregator, DTO_Device, DTO_Metric, DTO_Snapshot
import requests
from datetime import datetime, timezone
import psutil
import logging
from typing import Callable, List
import os
import platform
import hashlib
from my_logging.logger import setup_logging # type: ignore
import uuid
from collections import deque

logger = logging.getLogger(__name__)

# defining metric functions
def cpu_metric_function() -> DTO_Metric:
    logger.debug("Getting CPU Metric")
    return DTO_Metric(name="CPU Percent", value=psutil.cpu_percent(interval=1))

def ram_metric_function() -> DTO_Metric:
    logger.debug("Getting RAM Metric")
    return DTO_Metric(name="RAM Usage", value=psutil.virtual_memory().percent)

class DeviceHandler:
    def __init__(self, name):
        logger.debug("Initializing DeviceHandler with name: %s", name)
        self.device = DTO_Device(name=name, snapshots=[])
        self.metric_functions: List[Callable[[], DTO_Metric]] = []

    def register_metric_function(self, func: Callable[[], DTO_Metric]):
        logger.debug("Registering Metric Function: %s", func.__name__)
        self.metric_functions.append(func)

    def capture(self) -> DTO_Snapshot:
        logger.info("Capturing Snapshot")
        
        timestamp = datetime.now()
        logger.debug("Timestamp set: %s", timestamp)
        
        timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()
        timezone_mins = int(timezone_offset.total_seconds() / 60)
        logger.debug("Timezone Offset set: %s", timezone_mins)
        
        metrics = [func() for func in self.metric_functions]
        logger.debug("Metrics set: %s", metrics)
        
        snapshot = DTO_Snapshot(timestamp_capture=timestamp, timezone_mins=timezone_mins, metrics=metrics)
        logger.info("Snapshot Captured")
        
        self.device.snapshots.append(snapshot)
        return snapshot

class AggregatorHandler:
    def __init__(self, deviceHandlers: List[DeviceHandler]):
        logger.debug("Initializing AggregatorHandler")
        self.aggregator = DTO_Aggregator(
            guid=self.get_machine_uuid(),
            name=platform.node(),
            devices=[handler.device for handler in deviceHandlers])
        self.device_handlers = deviceHandlers
        self.post_queue = deque()

    def register_device(self, device_handler: DeviceHandler):
        logger.debug("Registering DeviceHandler: %s", device_handler.device.name)
        self.device_handlers.append(device_handler)
        self.aggregator.devices.append(device_handler.device)
    
    def get_machine_uuid(self):
        logger.debug("Getting machine UUID")
        system = platform.system()
        if system == "Windows":
            node = platform.node()
            mac = uuid.getnode()
            unique_str = f"{node}-{mac}"
        elif system == "Darwin":
            node = platform.node()
            mac = uuid.getnode()
            unique_str = f"{node}-{mac}"
        elif system == "Linux":
            node = platform.node()
            mac = uuid.getnode()
            unique_str = f"{node}-{mac}"
        else:
            logger.error("Unsupported platform: %s", system)
            unique_str = str(uuid.uuid4())

        # Hash the unique string to generate a UUID
        unique_hash = hashlib.sha256(unique_str.encode()).hexdigest()
        logger.debug("Generated UUID: %s", unique_hash[:32])
        return str(uuid.UUID(unique_hash[:32]))
  
    def capture(self):
        logger.info("Capturing data from all registered devices")
        for device_handler in self.device_handlers:
            device_handler.capture()
        self.post_queue.append(self.aggregator.to_json())

    def post_aggregator(self, url: str):
        if not self.post_queue:
            logger.info("No data to post")
            return None
        
        logger.info("Queue length: %s", len(self.post_queue))
        aggregator_json = self.post_queue.popleft()
        logger.debug("Aggregator JSON object: %s", aggregator_json)
        
        try:
            response = requests.post(url, json=aggregator_json)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            logger.info("Aggregator data posted successfully")
            logger.info("Response text: %s", response.text)
            logger.debug("Response status code: %s", response.status_code)
            return response
        except requests.exceptions.RequestException as e:
            logger.error("Connection error occurred: %s", e)
            
            # Re-add the JSON to the front of the queue if a connection error occurs
            logger.debug("Readding JSON to the front of the queue")
            self.post_queue.appendleft(aggregator_json)
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error occurred: %s", e)
            logger.error("Failed to post aggregator data with error code: %s", response.status_code)
            logger.info("Response text: %s", response.text)
            logger.debug("Response status code: %s", response.status_code)
            # Do not re-add the JSON to the queue if a server/data error occurs
        return None
