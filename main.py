from src.logger import setup_logging
from src.snapshot import take_snapshot

def main():
    setup_logging()
    take_snapshot()

if __name__ == "__main__":
    main()