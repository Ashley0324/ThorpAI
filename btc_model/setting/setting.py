import os
from logging import CRITICAL
from typing import Dict, Any
from tzlocal import get_localzone
from btc_model.core.util.file_util import FileUtil

SETTINGS: Dict[str, Any] = {
    # 配置request url需要的proxies，如果网络环境无需代理，注释即可
    # "common.proxies": {
    #     'http': 'http://127.0.0.1:52469',
    #     'https': 'http://127.0.0.1:52469'
    # },


    "font.family": "微软雅黑",
    "font.size": 12,

    "log.active": True,
    "log.level": CRITICAL,
    "log.console": True,
    "log.file": True,

    "email.server": "smtp.qq.com",
    "email.port": 465,
    "email.username": "",
    "email.password": "",
    "email.sender": "",
    "email.receiver": "",

    "cex.okx.apikey": "8458f3f2-2336-45a6-8478-5faadb1faeb8",
    "cex.okx.secretkey": "C3D924B57DE38D9A3466139B4814C8D0",
    "cex.okx.passphrase": "970410Sjw.",
    # 配置okx用的代理，若网络网络无需代理，设置为None
    # "cex.okx.proxy": "http://127.0.0.1:52469",
    "cex.okx.proxy": None,

    "cex.binance.apikey": "3JIn0k7ZcTdR6bvPmWzf4Ha294rJqWvN2h69wyRc7ETbVKIiot8GOqEC6vjJYOuC",
    "cex.binance.secretkey": "FkeW6gIYUAjrIhFRT7RFsT5950WsudstML8aoOFQqwLLoy3ukCIM9LRrXsRwk9WO",

    # ------------------------------------------------------
    # 设置逃顶模型各指标的参数
    # ------------------------------------------------------
    "escape_model.indicator.pi_cycle.short_window": 111,
    "escape_model.indicator.pi_cycle.long_window": 350,
    "escape_model.indicator.pi_cycle.threshold": 2,

    "escape_model.indicator.mvrv_zscore.threshold": 8,

    "escape_model.indicator.mayer_multiple.window": 200,
    "escape_model.indicator.mayer_multiple.threshold": 2.4,

    "escape_model.indicator.feargreed.threshold": 80,

    "escape_model.indicator.rsi.window": 14,
    "escape_model.indicator.rsi.upper": 70,
    "escape_model.indicator.rsi.lower": 30,

    "escape_model.indicator.macd.fast_period": 12,
    "escape_model.indicator.macd.slow_period": 26,
    "escape_model.indicator.macd.signal_period": 9,

    "escape_model.indicator.sth_mvrv.threshold": 2,

    "escape_model.indicator.bollinger.window": 100,
    "escape_model.indicator.bollinger.nbdev": 2.5,
    # ------------------------------------------------------

    # ------------------------------------------------------
    # update_manager的参数
    # ------------------------------------------------------
    "update_manager.indicator.use_exchange": 'OKX',
    "update_manager.indicator.symbols": ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'SOL-USDT'],


    "database.uri": "",
    "database.name": "",
    "database.database": "",
    "database.host": "",
    "database.port": 0,
    "database.user": "",
    "database.password": "",
    "database.auth_source": ''
}


# Load global setting from json file.
# SETTING_FILENAME: str = "blockchain_setting.json"
# SETTINGS.update(FileUtil.load_json(SETTING_FILENAME))


def get_settings(prefix: str = "") -> Dict[str, Any]:
    prefix_length = len(prefix)
    if prefix_length > 0 and not prefix.endswith('.'):
        prefix = prefix + '.'
        prefix_length += 1

    return {k[prefix_length:]: v for k, v in SETTINGS.items() if k.startswith(prefix)}

