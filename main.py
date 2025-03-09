from my_logging.logger import setup_logging # type: ignore
from src.capture_client import DeviceHandler, AggregatorHandler, cpu_metric_function, ram_metric_function 
import logging
import json
from src.config import Config 
import time

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Application")
    
    config = Config("config.json")
    
    aggregator_handler = AggregatorHandler(deviceHandlers=[])
    windows_device_handler = DeviceHandler("WindowsOS")
    windows_device_handler.register_metric_function(cpu_metric_function)
    windows_device_handler.register_metric_function(ram_metric_function)
    aggregator_handler.register_device(windows_device_handler)
    logging.info("Starting capture loop")
    while True:
        #logic here to send a capture to the server every 5 seconds
        logger.info("Starting capture")
        aggregator_handler.capture()
        logger.info("Capture completed")
        
        logger.debug("Aggregator data: %s", aggregator_handler.aggregator.to_json())
        
        post_url = "%s%s" % (config.web_host, config.post_api_endpoint)
        
        logger.info("Beginning post")
        logger.debug("Calling post to URL: %s", post_url)
        aggregator_handler.post_aggregator(post_url)
        logger.info("Post completed")
        
        logger.info("Sleeping for %s seconds", config.capture_interval)
        time.sleep(config.capture_interval)

    logging.info("Application Completed Successfully") 
if __name__ == "__main__":
    main()