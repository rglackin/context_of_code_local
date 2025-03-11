from src.config import Config
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

def get_ticker_price(ticker_name: str):
    # Get the ticker of the stock
    try:
        
        ticker = yf.Ticker(ticker_name)
    
        # Get the current price of the stock
        ticker_price = ticker.history(period="1d")["Close"].iloc[-1]
        if ticker_price:
            logger.info("Current price of %s is %s USD", ticker_name, ticker_price)
            return ticker_price
        logger.error("Failed to retrieve %s price data. May be rate limited or unavailable", ticker_name)
    except Exception as e:
        logger.error("Failed to retrieve %s price data: %s", ticker_name, e)
    return None