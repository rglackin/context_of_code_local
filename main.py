from my_logging.logger import setup_logging # type: ignore
from src.capture_client import DeviceHandler, AggregatorHandler, cpu_metric_function, ram_metric_function, stock_tick_metric_function, bitcoin_ticker_metric_function 
import logging
import json
from src.config import Config 
import time
import requests

# def read_json_file(file_path):
#     with open(file_path, 'r') as file:
#         data = json.load(file)
#     return data
logger = logging.getLogger(__name__)

def get_stock_symbols(url):
    try:
        response = requests.get(url)
        logger.info("GET Stock response code: %s", response.status_code)
        logger.info("GET Stock response: %s", response.text)
        response.raise_for_status()
        data = response.json()
        logger.info("GET Stock returned: %s", data)
        return data.get("symbols", [])
    except requests.RequestException as e:
        logger.error("Failed to retrieve stock symbols: %s", e)
        return []

def create_stock_metric_function(symbol):
    def stock_metric_function():
        return stock_tick_metric_function(symbol)
    stock_metric_function.__name__ = f'stock_tick_metric_function_{symbol}'
    return stock_metric_function

def update_stock_symbols(stock_device_handler, new_symbols):
    current_symbols = {func.__name__.split('_')[-1] for func in stock_device_handler.metric_functions if func.__name__.startswith('stock_tick_metric_function')}
    logger.info("Current stock symbols: %s", current_symbols)
    
    # Deregister stocks that are not in the new list
    for symbol in current_symbols - set(new_symbols):
        stock_device_handler.metric_functions = [func for func in stock_device_handler.metric_functions if func.__name__ != f'stock_tick_metric_function_{symbol}']
        logger.info("Deregistered stock symbol: %s", symbol)
    
    # Register new stocks
    for symbol in set(new_symbols) - current_symbols:
        stock_device_handler.register_metric_function(create_stock_metric_function(symbol))
        logger.info("Registered stock symbol: %s", symbol)


def main():
    setup_logging()
    
    logger.info("Starting Application")
    
    config = Config("config.json")
    
    aggregator_handler = AggregatorHandler(deviceHandlers=[])
    windows_device_handler = DeviceHandler("WindowsOS")
    windows_device_handler.register_metric_function(cpu_metric_function)
    windows_device_handler.register_metric_function(ram_metric_function)
    
    stock_device_handler = DeviceHandler("Yahoo Finance")
    for _, symbol in config.stock_symbols.items():
        logger.info("Registering stock symbol: %s", symbol)
        stock_device_handler.register_metric_function(create_stock_metric_function(symbol))
    # stock_device_handler.register_metric_function(lambda: stock_tick_metric_function(config.stock_symbol))
    stock_device_handler.register_metric_function(bitcoin_ticker_metric_function)
    aggregator_handler.register_device(windows_device_handler)
    aggregator_handler.register_device(stock_device_handler)
    
    stock_symbols_url = "%sapi/stock-symbols" % config.web_host
    
    logging.info("Starting capture loop")
    i = 1
    while True:
        # Poll the endpoint to get the stock symbols
        logger.info("Polling stock symbols at %s", stock_symbols_url)
        new_symbols = get_stock_symbols(stock_symbols_url)
        if new_symbols:
            logger.info("New stock symbols: %s", new_symbols)
            update_stock_symbols(stock_device_handler, new_symbols)
        
        #logic here to send a capture to the server every 5 seconds
        logger.info("Starting capture")
        aggregator_handler.capture()
        logger.info("Capture completed")
        
        logger.debug("Capture count for this session: %s", i)
        i+=1
        
        logger.debug("Aggregator data: %s", aggregator_handler.aggregator.to_json())
        
        post_url = "%s%s" % (config.web_host, config.post_api_endpoint)
        
        logger.info("Posting to server")
        logger.debug("Calling post to URL: %s", post_url)
        aggregator_handler.post_aggregator(post_url)
        logger.info("Post complete")
        
        logger.info("Sleeping for %s seconds", config.capture_interval)
        time.sleep(config.capture_interval)

    logging.info("Application Completed Successfully") 
if __name__ == "__main__":
    main()