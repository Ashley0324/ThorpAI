import pandas as pd
import btcmodel as model
import requests
import json


# input parameters for PI Model
pi_model_max_days = 350
pi_model_min_days = 111

# input parameters for Mayer Model
mayer_model_days = 200

pi_model_sum_max = model.BTCCalculationProcess(pi_model_max_days)
btc_price_sum_350 = pi_model_sum_max.calc_btc_price_sum_in_period()

pi_model_sum_min = model.BTCCalculationProcess(pi_model_min_days)
btc_price_sum_111 = pi_model_sum_min.calc_btc_price_sum_in_period()

mayer_model_sum = model.BTCCalculationProcess(mayer_model_days)
btc_price_sum_200 = mayer_model_sum.calc_btc_price_sum_in_period()

#escape_flag_pi_model = model.CalcPIModelResult(btc_price_sum_111, btc_price_sum_350)
escape_flag_mayer_model = model.CalcMayerModelResult(btc_price_sum_200)

# print(escape_flag_pi_model)
print(escape_flag_mayer_model)
