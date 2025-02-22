import psutil
import logging

logger = logging.getLogger(__name__)

def take_snapshot():
    ram_usage = psutil.virtual_memory().percent
    net_io = psutil.net_io_counters()
    logger.info(f"RAM Usage: {ram_usage}%")
    logger.info(f"Net IO - Bytes Sent: {net_io.bytes_sent}, Bytes Received: {net_io.bytes_recv}")