import time
import psutil
import logging
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass
@dataclass_json
class DataSnapshot:
    metrics:dict
    def __init__(self, metrics=None):
        if metrics is None:
            self.metrics = {
                'ram_usage': None,
                'cpu_percent': None,
            }
        else:
            self.metrics = metrics
        self.logger = logging.getLogger(__name__)
        self.net_io = None

    def take_snapshot(self):
        self.logger.debug("Taking snapshot of system data")
        start_time = time.time()
        self.metrics['ram_usage'] = psutil.virtual_memory().percent
        self.metrics['cpu_percent'] = psutil.cpu_percent()
        end_time = time.time()
        self.logger.info("Snapshot taken in %s seconds", str(end_time - start_time))
        [self.logger.debug("Snapshot taken? %s: %s", key, str(value is not None)) for key, value in self.metrics.items()]

    # def log_snapshot(self):
    #     self.logger.info(f"RAM Usage: {self.ram_usage}%")
    #     self.logger.info(f"{self.logger.handlers}")
    #     self.logger.info(f"Net IO - Bytes Sent: {self.net_io.bytes_sent}, Bytes Received: {self.net_io.bytes_recv}")