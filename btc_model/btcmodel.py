import pandas as pd
import json
import okx.MarketData as MarketData

## API initialize
apikey = "8458f3f2-2336-45a6-8478-5faadb1faeb8"   #  初始化API密钥
secretkey = "C3D924B57DE38D9A3466139B4814C8D0"    #  初始化API密钥
IP = "192.168.3.57"                               #  初始化IP地址
passphrase = "970410Sjw."                         #  个人密码

## config definition
api_max_data_size_once = 100
one_day_in_ms = 86400000

## Get Info From API
flag = "0"                                        # 实盘:0 , 模拟盘:1
marketDataAPI = MarketData.MarketAPI(
    api_key=apikey, api_secret_key=secretkey, passphrase=passphrase, flag=flag)
btc_price = marketDataAPI.get_index_tickers(instId="BTC-USD")

def CalcPIModelResult(btc_price_sum_111, btc_price_sum_350):
    current_111_average = btc_price_sum_111 / 111
    current_350_average = btc_price_sum_350 / 350
    escape_flag_pi_model = False
    if current_111_average > 2 * current_350_average:
        escape_flag_pi_model = True
    return escape_flag_pi_model

def CalcMayerModelResult(btc_price_sum_200):
    current_200_average = btc_price_sum_200 / 200
    current_btc_info = marketDataAPI.get_index_tickers(instId="BTC-USD")
    btc_kline_dict = json.dumps(current_btc_info)
    btc_kline_price_current = btc_kline_dict['data']['open24h'][0]
    escape_flag_mayer_model = False
    if btc_kline_price_current > 2.4 * current_200_average:
        escape_flag_mayer_model = True
    return escape_flag_mayer_model

class BTCCalculationProcess :
    def __init__(self, period_days):
        self.period_need_calc = period_days
    def calc_btc_price_sum_in_period(self):
        pi_model_days = self.period_need_calc
        total_loop_count = (pi_model_days // api_max_data_size_once) + 1
        rest_days = pi_model_days % api_max_data_size_once
        temp_k_line_sum = 0

        for i in range(total_loop_count):
            if i == 0:
                btc_k_line_100 = marketDataAPI.get_index_candlesticks(instId="BTC-USD", bar="1D")
                btc_k_line_100_df = pd.DataFrame(btc_k_line_100)
                df_size = btc_k_line_100_df['data'].size
                for index in range(df_size):
                    temp_k_line_sum += float(btc_k_line_100_df['data'][index][4])
                    if index == df_size - 1:
                        ts_100 = btc_k_line_100_df['data'][index][0]
            elif i == total_loop_count - 1:
                btc_k_line_100 = marketDataAPI.get_index_candlesticks(instId="BTC-USD", bar="1D",
                                                                      after=ts_100, limit=rest_days)
                btc_k_line_100_df = pd.DataFrame(btc_k_line_100)
                df_size = btc_k_line_100_df['data'].size
                for index in range(df_size):
                    temp_k_line_sum += float(btc_k_line_100_df['data'][index][4])
            else:
                btc_k_line_100 = marketDataAPI.get_index_candlesticks(instId="BTC-USD", bar="1D", after=ts_100)
                btc_k_line_100_df = pd.DataFrame(btc_k_line_100)
                df_size = btc_k_line_100_df['data'].size
                for index in range(df_size): 
                    temp_k_line_sum += float(btc_k_line_100_df['data'][index][4])
                    if index == df_size - 1:
                        ts_100 = btc_k_line_100_df['data'][index][0]
        return(temp_k_line_sum)