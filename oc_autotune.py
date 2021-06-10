import pandas as pd
import numpy as np
import datetime as dt
import pytz

from dateutil.relativedelta import relativedelta

# from sklearn.model_selection import ParameterGrid
import sqlite3

from library.modules.api import HiveOSApi
from library.modules.code_patterns import AttDict
from library.modules.config import ConfigBase
from library.modules.misc import join_dicts


def autenticate(config: AttDict) -> dict:
    return {'conection': True}


def get_gpus(api: any, config: AttDict) -> dict:
    return {}


def get_metrics(api: any, gpu: str, config: AttDict) -> pd.DataFrame:
    return pd.DataFrame()


now = dt.datetime.now(tz=pytz.timezone('Europe/Madrid'))
config = ConfigBase('data/config.yaml')
api = HiveOSApi(config)
# farms = api.farms()
# farm = api.farm('543234')
for farm_id in config.farms_to_autooc:
    all_gpus = api.gpus(farm_id)
    for worker in api.workers(farm_id):
        gpus = [gpu for gpu in all_gpus
                if gpu['worker']['id'] == worker['id']]
        all_metrics = api.metrics(farm_id, worker['id'])
        for gpu in gpus:
            i = gpu['index']
            metrics = [join_dicts({'time': d['time'],
                                   'fan': d['fan'][i],
                                   'temp': d['temp'][i],
                                   'power': d['power_list'][i],
                                   'total_power': d['power']},
                                  {})
                       for d in all_metrics]
        print('developping...')
db = sqlite3.connect('data/gpu_metrics.db')

for gpu, gpu_attributes in gpus.items():
    print(f'Checking gpu {gpu}')
    metrics = get_metrics(api, gpu, config)

print('The end')
