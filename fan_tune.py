import re

from library.modules.api import HiveOSApi
from library.modules.code_patterns import AttDict
from library.modules.config import ConfigBase
from library.modules.misc import execute_bash


def autenticate(config: AttDict) -> dict:
    return {'conection': True}


def get_fans() -> dict:
    nvidia_info, err, rc = execute_bash('nvidia-info')
    assert not err, err
    assert not rc, rc

    gpus_pattern = re.compile("GPU (\d),")
    fans_pattern = re.compile("Fan (\d\d) %")

    gpus = gpus_pattern.findall(nvidia_info)
    fans = fans_pattern.findall(nvidia_info)
    gpus_fan_speeds = {gpu: fan_speed for gpu, fan_speed in zip(gpus, fans)}

    return gpus_fan_speeds


config = ConfigBase('data/config.yaml')
api = HiveOSApi(config)
farms = api.farms()
farm = api.farm('543234')
# all_gpus = api.gpus(farm_id)
# power_limits = worker['overclock']['nvidia']['power_limit'].split()
for farm_id in config.farms_to_autooc:
    for worker in api.workers(farm_id):
        print(f"farm id: {farm_id} worker id: {worker['id']}")

        model_short_names = {gpu['bus_number']: gpu['short_name']
                             for gpu in worker['gpu_info']
                             if 'short_name' in gpu}
        gpu_indexes = {gpu['bus_number']: gpu['index']
                             for gpu in worker['gpu_info']
                             if 'index' in gpu}
        gpus_info = [{'short_name': model_short_names[stats['bus_number']],
                      'bus_number': stats['bus_number'],
                      'index': gpu_indexes[stats['bus_number']],
                      'power': stats['power'],
                      'fan': stats['fan'],
                      'hash': stats['hash'] / 10 ** 3,
                      'power_limit': config.power_limit[model_short_names[stats['bus_number']]],
                      'fan_limit': config.fans_limit[model_short_names[stats['bus_number']]],
                      'hash_objective': config.hash_objective[model_short_names[stats['bus_number']]]}
                     for stats in worker['gpu_stats']]

        power_overclock = []
        indexes = []
        for gpu in sorted(gpus_info, key=lambda gpu: gpu['bus_number']):
            initial_power = gpu['power']
            power = gpu['power']
            fan_delta = gpu['fan'] - gpu['fan_limit']
            if gpu['fan'] > gpu['fan_limit']:
                if fan_delta >= 10:
                    power -= 5
                elif fan_delta >= 5:
                    power -= 3
                elif fan_delta >= 2:
                    power -= 1
            elif (gpu['power'] < gpu['power_limit']) and (gpu['hash'] <= gpu['hash_objective']):
                if fan_delta <= 10:
                    power += 5
                elif fan_delta <= 5:
                    power += 3
                elif fan_delta <= 2:
                    power += 1
            else:
                pass
            if power != initial_power:
                print(f"Gpu {gpu['short_name']} bus {gpu['bus_number']} fan excess {fan_delta} "
                      f"power goes from {initial_power} to {power}")
            power_overclock.append(str(power))
            indexes.append(str(gpu['index']))
        # power_overclock = ' '.join(power_overclock)
        # indexes = ','.join(indexes)
        core_clocks = worker['overclock']['nvidia']['core_clock'].split()
        mem_clocks = worker['overclock']['nvidia']['mem_clock'].split()
        print(power_overclock)
        api.set_oc(farm_id=farm_id, worker_id=worker['id'],
                   indexes=indexes, power_limits=power_overclock,
                   core_clocks=core_clocks,
                   mem_clocks=mem_clocks)

print('The end')
