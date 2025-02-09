from dataclasses import dataclass
from btc_model.core.common.const import (InstrumentType,
                                         Product,
                                         Exchange
                                         )

@dataclass
class Instrument:
    instrument_id: str
    instrument_name: str
    exchange: Exchange
    instrument_type: InstrumentType
    product: Product
    list_date: str
    expire_date: str
    price_tick: float
    min_limit_order_volume: float
    max_limit_order_volume: float
    min_market_order_volume: float
    max_market_order_volume: float
    status: str



