import json
from typing import List

import requests as requests

from library.modules.code_patterns import AttDict


class HiveOSApi:
    baseUrl = 'https://api2.hiveos.farm/api/v2'

    def __init__(self, config: AttDict):
        # self.username = config.username
        # self.password = config.password
        self.headers = config.headers

        # account = self.get_account()
        # auth = self.login()
        # self.token = auth.access_token

    def get(self, url: str, params: dict):
        response = requests.get(url=f'{self.baseUrl}/{url}',
                                headers=self.headers,
                                params=params)
        return json.loads(response.content)

    def post(self, url: str, body: dict):
        # import json
        # json_object = json.dumps(body, indent=4)
        return requests.post(url=f'{self.baseUrl}{url}',
                             headers=self.headers,
                             # data=body)
                             json=body)

    # def login(self):
    #     return self.post('auth/login',
    #                      body={"login": self.username,
    #                            "password": self.password,
    #                            "twofa_code": "234345",
    #                            "remember": 'true'})

    def get_account(self):
        return self.get('account', {})

    def farms(self, tags: List[str] = None):
        response = self.get('farms', {})
        return response['data']

    def farm(self, id: str):
        response = self.get(f'farms/{id}', {})
        return response

    def workers(self, farm_id: str):
        response = self.get(f'farms/{farm_id}/workers', {})
        return response['data']

    def gpus(self, farm_id: str):
        response = self.get(f'farms/{farm_id}/workers/gpus', {})
        return response['data']

    def metrics(self, farm_id: int, worker_id: int):
        response = self.get(f'farms/{farm_id}/workers/{worker_id}/metrics', {})
        return response['data']

    def get_oc(self, farm_id: int, worker_id: int):
        response = self.get(f'farms/{farm_id}/oc', {})
        return response['data']

    def set_oc(self, farm_id: int, worker_id: int, indexes: list, power_limits: list, core_clocks: list, mem_clocks: list):
        response = self.post(f'/farms/{farm_id}/workers/overclock',
                             {"gpu_data": [{"gpus": [{"worker_id": worker_id,
                                                      "gpu_index": indexes[i]
                                                      }
                                                     ],
                                            "nvidia": {"core_clock": int(core_clocks[i]),
                                                       "mem_clock": int(mem_clocks[i]),
                                                       "fan_speed": 0,
                                                       "power_limit": int(power_limits[i])
                                                       }
                                            }
                                           for i in range(len(indexes))]
                              }
                             )
        return response
