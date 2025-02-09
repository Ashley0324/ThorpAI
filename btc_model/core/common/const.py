from enum import Enum

PROJECT_NAME = 'ThorpAI'


class Interval(Enum):
    """
    interval of bar data.
    """
    NONE = "NONE"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    TICK = "tick"


class InstrumentType(Enum):
    STOCK = 'STOCK'
    FUTURE = 'FUTURE'
    OPTION = 'OPTION'
    BOND = 'BOND'
    OPENFUND = 'OF'
    ETF = 'ETF'
    INDEX = 'INDEX'
    CRYPTO = 'CRYPTO'


class Product(Enum):
    # 股指期货

    # 商品期货

    # 加密货币
    SPOT = 'SPOT'  # Spot
    MARGIN = 'MARGIN'  # Margin
    SWAP = 'SWAP'  # Perpetual Futures
    FUTURES = 'FUTURES'  # Expiry Futures
    OPTION = 'OPTION'  # Option


class Exchange(Enum):
    """
    Exchange.
    """
    NONE = ""
    # Chinese
    SSE = "SSE"  # Shanghai Stock Exchange
    SZSE = "SZSE"  # Shenzhen Stock Exchange

    CFFEX = "CFFEX"  # China Financial Futures Exchange
    SHFE = "SHFE"  # Shanghai Futures Exchange
    CZCE = "CZCE"  # Zhengzhou Commodity Exchange
    DCE = "DCE"  # Dalian Commodity Exchange
    INE = "INE"  # Shanghai International Energy Exchange

    BSE = "BSE"  # Beijing Stock Exchange
    CFETS = "CFETS"  # CFETS Bond Market Maker Trading System
    XBOND = "XBOND"  # CFETS X-Bond Anonymous Trading System

    # Global
    NYSE = "NYSE"  # New York Stock Exchnage
    NASDAQ = "NASDAQ"  # Nasdaq Exchange
    HKEX = "HKEX"  # Stock Exchange of Hong Kong

    # Crypto Currency
    BINANCE = "BINANCE"  # BINANCE Exchange
    OKX = "OKX"  # OKX Exchange


class ProviderType(Enum):
    """
    数据提供方
    """
    NONE = 'NONE'
    ALTERNATIVE = 'ALTERNATIVE'
    BLOCKCHAIN = 'BLOCKCHAIN'  # https://api.blockchain.com/
    BITCOIN_DATA = 'BITCOIN_DATA'  # https://bitcoin-data.com
    GLASSNODE = 'GLASSNODE'
    BINANCE = 'BINANCE'
    OKX = 'OKX'


class EntityType(Enum):
    INSTRUMENT = 'INSTRUMENT'
    KLINE = 'KLINE'
    KLINE_INDEX = 'KLINE_INDEX'
    INDICATOR = 'INDICATOR'
    FACTOR = 'FACTOR'
    FEATURE = 'FEATURE'
    ORDER = 'ORDER'
    TRADE = 'TRADE'
    ACCOUNT = 'ACCOUNT'
