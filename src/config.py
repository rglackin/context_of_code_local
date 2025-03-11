import json

class Config:
    def __init__(self, config_file: str):
        with open(config_file, 'r') as file:
            config_data = json.load(file)
        self.capture_interval = config_data.get("capture_interval")
        self.web_host = config_data.get("web_host")
        self.post_api_endpoint = config_data.get("post_api_endpoint")
        self.stock_symbols = config_data.get("stock_symbols")