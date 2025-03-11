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
from src.stock_ticker import get_ticker_price

logger = logging.getLogger(__name__)

# defining metric functions
def cpu_metric_function() -> DTO_Metric:
    logger.debug("Getting CPU Metric")
    return DTO_Metric(name="CPU Percent", value=psutil.cpu_percent(interval=1))

def ram_metric_function() -> DTO_Metric:
    logger.debug("Getting RAM Metric")
    return DTO_Metric(name="RAM Usage", value=psutil.virtual_memory().percent)

def stock_tick_metric_function(stock_name: str) -> DTO_Metric:
    logger.debug("Getting Stock Tick Metric")
    stock_price = get_ticker_price(stock_name)
    return DTO_Metric(name=("Stock Price (%s)" % stock_name), value=stock_price)

def bitcoin_ticker_metric_function() -> DTO_Metric:
    logger.debug("Getting Bitcoin Ticker Metric")
    btc_name = "BTC-USD"
    bitcoin_price = get_ticker_price(btc_name)
    return DTO_Metric(name=btc_name, value=bitcoin_price)

class DeviceHandler:
    def __init__(self, name):
        logger.debug("Initializing DeviceHandler with name: %s", name)
        self.device = DTO_Device(name=name, snapshots=[])
        self.metric_functions: List[Callable[[], DTO_Metric]] = []

    def register_metric_function(self, func: Callable[[], DTO_Metric]):
        logger.debug("Registering Metric Function: %s", func.__name__)
        self.metric_functions.append(func)

    def capture(self) -> DTO_Snapshot:
        logger.info("Capturing Snapshot for %s", self.device.name)
        
        timestamp = datetime.now()
        logger.debug("Timestamp set: %s", timestamp)
        
        timezone_offset = datetime.now(timezone.utc).astimezone().utcoffset()
        timezone_mins = int(timezone_offset.total_seconds() / 60)
        logger.debug("Timezone Offset set: %s", timezone_mins)
        
        metrics = [func() for func in self.metric_functions]
        metrics = [metric for metric in metrics if metric.value is not None]
        if not metrics:
            logger.warning("No metrics captured")
            return None
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
            # name="Test aggregator",
            name=platform.node(),
            devices=[handler.device for handler in deviceHandlers])
        self.device_handlers = deviceHandlers
        self.snapshot_queue = deque()

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
        # unique_str = str(uuid.uuid4())

        # Hash the unique string to generate a UUID
        unique_hash = hashlib.sha256(unique_str.encode()).hexdigest()
        logger.debug("Generated UUID: %s", unique_hash[:32])
        return str(uuid.UUID(unique_hash[:32]))
  
    def capture(self):
        logger.info("Capturing data from all registered devices")
        for device_handler in self.device_handlers:
            snapshot = device_handler.capture()
            if snapshot:
                self.snapshot_queue.append((device_handler.device.name, snapshot))
        logger.info("Snapshots appended to the queue")
        logger.debug("Queue items: %s", {ss.to_json() for _, ss in self.snapshot_queue})
        logger.debug("Queue length: %s", len(self.snapshot_queue))

    def post_aggregator(self, url: str):
        logger.info("Posting aggregator data to URL: %s", url)
        if not self.snapshot_queue:
            logger.info("No data to post")
            return None
        
        logger.info("Queue length: %s", len(self.snapshot_queue))
        
        while self.snapshot_queue:
            device_name, snapshot = self.snapshot_queue.popleft()
            temp_aggregator = DTO_Aggregator(
                guid=self.aggregator.guid,
                name=self.aggregator.name,
                devices=[DTO_Device(name=device_name, snapshots=[snapshot])]
            )
            aggregator_json = temp_aggregator.to_json()
            logger.debug("Attempting to post Aggregator JSON object: %s", aggregator_json)
            connected_successfully = False
            try:
                response = requests.post(url, json=aggregator_json)
                logger.info("Response received")
                connected_successfully = True
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
                logger.info("Aggregator data posted successfully for device: %s", device_name)
                logger.info("Response text: %s", response.text)
                logger.debug("Response status code: %s", response.status_code)
                
                # Remove the snapshot that was posted from the aggregator object
                self.remove_snapshot(device_name, snapshot)
                
            except requests.exceptions.RequestException as e:
                if connected_successfully:
                    logger.error("Snapshot caused server error, dropping it: %s", e)
                    self.remove_snapshot(device_name, snapshot)
                else:
                    # Do not remove snapshot from the queue if a connection error occurs
                    logger.error("Connection error occurred: %s", e)
                    self.snapshot_queue.appendleft((device_name, snapshot))
                    break
        logger.info("Queue length: %s", len(self.snapshot_queue))
        return None

    def remove_snapshot(self, device_name, snapshot):
        for device in self.aggregator.devices:
            if device.name == device_name:
                device.snapshots.remove(snapshot)
    
    # def flush_queue(self, url: str):
    #     logger.info("Flushing the post queue")
    #     while self.snapshot_queue:
    #         self.post_aggregator(url)
if __name__ == "__main__":
    setup_logging()
    logger.info("Starting capture client")

    device_handler = DeviceHandler("WinOS")
    device_handler.register_metric_function(cpu_metric_function)
    device_handler.register_metric_function(ram_metric_function)
    # Register stock tick metric function with a specific stock name
    stock_name = "AAPL"
    device_handler.register_metric_function(lambda: stock_tick_metric_function(stock_name))
    
    agg_handler = AggregatorHandler([device_handler])
    agg_handler.capture()
    time.sleep(5)
    agg_handler.capture()
    agg_handler.post_aggregator("http://localhost:5000/api/v1/aggregator")
    agg_handler.flush_queue("http://localhost:5000/api/v1/aggregator")
    logger.info("Application Completed Successfully")