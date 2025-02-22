import logging
import json
import os

class JsonFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.filename = filename
        self._open_file()

    def _open_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def emit(self, record):
        log_entry = self.format(record)
        if isinstance(record.msg, dict):
            log_entry = json.dumps(record.msg)
        with open(self.filename, 'r+') as f:
            f.seek(0)
            data = f.read().strip()
            if data == '[]':
                f.seek(0)
                f.write('[' + log_entry + ']')
            else:
                f.seek(0)
                data = data[:-1] + ',' + log_entry + ']'
                f.write(data)