# -*- coding: utf-8 -*
import pandas as pd
from tqdm import tqdm
from time import sleep
import requests, time, hmac, hashlib, json, os
from urllib.parse import urlencode

recv_window = 5000
data_path = os.getcwd() + "/data/data.json"


class BinanceApiWrapper(object):
    BASE_URL = "https://www.binance.com/api/v1"
    FUTURE_URL = "https://fapi.binance.com/fapi/v1"
    BASE_URL_V3 = "https://api.binance.com/api/v3"
    PUBLIC_URL = "https://www.binance.com/exchange/public/product"

    __instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()

        return cls.__instance

    def ping(self):
        path = "%s/ping" % self.BASE_URL_V3
        return requests.get(path, timeout=180, verify=True).json()

    def get_ticker_price(self, market, rotate_count=0):
        path = "%s/ticker/price" % self.BASE_URL_V3
        params = {"symbol": market}
        res = self._get_no_sign(path, params)
        if res == 443 and rotate_count < 20:  # 网络问题并且20次都访问都是443则报错停止运行
            rotate_count += 1
            time.sleep(20)
            self.get_ticker_price(market, rotate_count)
        time.sleep(2)
        return float(res['price'])

    def get_ticker_24hour(self, market):
        path = "%s/ticker/24hr" % self.BASE_URL_V3
        params = {"symbol": market}
        res = self._get_no_sign(path, params)
        return res

    def get_market_data(self, symbol_id, interval, start_dt, end_dt, **kwargs):
        """
        获取Binance的K线数据
        :param symbol: 交易对，如 "BTCUSDT"
        :param interval: K线时间间隔，如 "1d" 表示每天
        :param start_time: 开始时间戳（毫秒）
        :param end_time: 结束时间戳（毫秒）
        :param limit: 返回的K线数量限制
        :return: K线数据列表
        """

        url = "%s/klines" % self.FUTURE_URL
        # 字符串的日期转换为datetime
        start_dt = int(pd.to_datetime(start_dt).timestamp() * 1000)
        end_dt = int(pd.to_datetime(end_dt).timestamp() * 1000)

        all_data = []
        received_rows = 0
        current_date = start_dt

        with tqdm() as pbar:
            while current_date < end_dt:
                params = {
                    'symbol': symbol_id,
                    'interval': interval,
                    'startTime': current_date,
                    'endTime': end_dt,
                    'limit': 1000  # 币安允许的最大请求条数
                }

                retries = 5
                for i in range(retries):
                    try:
                        response = requests.get(url, params=params)
                        break
                    except requests.exceptions.SSLError as e:
                        print(f"SSL error occurred: {e}. Retrying {i + 1}/{retries}...")
                        sleep(2)
                    except requests.exceptions.RequestException as e:
                        print(f"Request error: {e}. Retrying {i + 1}/{retries}...")
                        sleep(2)

                if response.status_code == 200:
                    data = response.json()
                    if not data:  # 如果没有更多数据，退出循环
                        break

                    df = pd.DataFrame(data)
                    received_rows += len(df)

                    all_data.append(df)

                    # 更新 current_date 为最早一条数据的时间
                    current_date = df.iloc[-1][6] + 1

                    # 添加延迟以避免超过 API 速率限制
                    time.sleep(0.1)
                else:
                    print("无法获取数据:", response.status_code, response.text)
                    return None

                pbar.update(received_rows)
                pbar.set_description(
                    f"fetching data from binance, symbol_id: {symbol_id}, received rows: {received_rows}")

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # final_df = final_df[final_df['Open Time'] <= start_dt]
            final_df.columns = [
                'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close Time', 'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
            ]
            final_df['Open Time'] = pd.to_datetime(final_df['Open Time'], unit='ms')
            final_df['Close Time'] = pd.to_datetime(final_df['Close Time'], unit='ms')
            final_df['symbol_id'] = symbol_id

            final_df = final_df.rename(columns={'Open Time': 'datetime',
                                                'Open': 'open',
                                                'High': 'high',
                                                'Low': 'low',
                                                'Close': 'close',
                                                'Quote Asset Volume': 'turnover',
                                                'Volume': 'volume'
                                                })

            final_df = final_df[['symbol_id', 'datetime', 'open', 'high', 'low', 'close', 'turnover', 'volume']]
            final_df[['open', 'high', 'low', 'close', 'turnover', 'volume']] = final_df[['open', 'high', 'low', 'close', 'turnover', 'volume']].astype(float)
            return final_df.sort_values('datetime').reset_index(drop=True)
        else:
            return None


    def buy_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "BUY", rate)
        return self._post(path, params)

    def sell_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "SELL", rate)
        return self._post(path, params)

    def buy_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "BUY")
        return self._post(path, params)

    def sell_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "SELL")
        return self._post(path, params)

    def get_ticker_24hour(self, market):
        path = "%s/ticker/24hr" % self.BASE_URL
        params = {"symbol": market}
        res = self._get_no_sign(path, params)
        print(res)
        return round(float(res['priceChangePercent']), 1)

    def get_positionInfo(self, symbol):
        '''当前持仓交易对信息'''
        path = "%s/positionRisk" % self.BASE_URL
        params = {"symbol": symbol}
        time.sleep(1)
        return self._get(path, params)

    def get_future_positionInfo(self, symbol):
        '''当前期货持仓交易对信息'''
        path = "%s/fapi/v2/positionRisk" % self.FUTURE_URL
        params = {"symbol": symbol}
        res = self._get(path, params)
        print(res)
        return res

    def dingding_warn(self, text):
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        api_url = "https://oapi.dingtalk.com/robot/send?access_token=%s" % self.dingding_token
        json_text = json_text = {
            "msgtype": "text",
            "at": {
                "atMobiles": [
                    "11111"
                ],
                "isAtAll": False
            },
            "text": {
                "content": text
            }
        }
        requests.post(api_url, json.dumps(json_text), headers=headers).content

    def get_cointype(self):
        '''读取json文件'''
        tmp_json = {}
        with open(data_path, 'r') as f:
            tmp_json = json.load(f)
            f.close()
        return tmp_json["config"]["cointype"]

    ### ----私有函数---- ###
    def _order(self, market, quantity, side, price=None):
        '''
        :param market:币种类型。如：BTCUSDT、ETHUSDT
        :param quantity: 购买量
        :param side: 订单方向，买还是卖
        :param price: 价格
        :return:
        '''
        params = {}

        if price is not None:
            params["type"] = "LIMIT"
            params["price"] = self._format(price)
            params["timeInForce"] = "GTC"
        else:
            params["type"] = "MARKET"

        params["symbol"] = market
        params["side"] = side
        params["quantity"] = '%.8f' % quantity

        return params

    def _get(self, path, params={}):
        params.update({"recvWindow": recv_window})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key}
        res = requests.get(url, headers=header, timeout=30, verify=True).json()
        if isinstance(res, dict):
            if 'code' in res:
                error_info = "报警：做多网格,请求异常.错误原因{info}".format(info=str(res))
                self.dingding_warn(error_info)
        return res

    def _get_no_sign(self, path, params={}):
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        # res = requests.get(url, timeout=10, verify=True).json()

        try:
            res = requests.get(url, timeout=10, verify=True).json()
            if isinstance(res, dict):
                if 'code' in res:
                    error_info = "报警：做多网格,请求异常.错误原因{info}".format(info=str(res))
                    self.dingding_warn(error_info)
            return res
        except Exception as e:
            if str(e).find("443") != -1:  # 网络错误不用报错
                return 443

    def _sign(self, params={}):
        data = params.copy()

        ts = int(1000 * time.time())
        data.update({"timestamp": ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        data.update({"signature": signature})
        return data

    def _post(self, path, params={}):
        params.update({"recvWindow": recv_window})
        query = self._sign(params)
        url = "%s" % (path)
        header = {"X-MBX-APIKEY": self.key}
        res = requests.post(url, headers=header, data=query, timeout=180, verify=True).json()

        if isinstance(res, dict):
            if 'code' in res:
                error_info = "报警：做多网格,请求异常.错误原因{info}".format(info=str(res))
                self.dingding_warn(error_info)

        return res

    def _format(self, price):
        return "{:.8f}".format(price)


if __name__ == "__main__":
    instance = BinanceApiWrapper()
    # print(instance.buy_limit("EOSUSDT",5,2))
    # print(instance.get_ticker_price("WINGUSDT"))
    start_dt = '2021-01-01 00:00:00'
    end_dt = '2024-11-15 23:59:59'
    result = instance.get_market_data("BTCUSDT", '5m', start_dt, end_dt)
    print(result)
