from src.logger import setup_logging
from src.snapshot import DataSnapshot
import logging
import json

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def main():
    setup_logging()
    snapshot = DataSnapshot()
    snapshot.take_snapshot()
    
    json_snapshot = snapshot.to_json()
    logging.debug("Logging Snapshot")
    logging.info(f"{(json_snapshot)}")
 
    # Can be used to read snapshot from json to object
    # logging.info("Reading JSON File")
    # file = read_json_file('logs/log.json')
    # file[-1]['message'] = json_snapshot
    # logging.info("JSON Snapshot Read From File")
    # snapshot = DataSnapshot.from_json(file[-1]['message'])
    # logging.info(f"{snapshot}")

    logging.info("Application Completed Successfully") 
if __name__ == "__main__":
    main()