import pandas as pd
import numpy as np
import datetime as dt

from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from pandas import option_context

from sklearn.model_selection import ParameterGrid


def calculate_cashout(df: pd.DataFrame, daily_earnings: float, minimum_cashout: int, max_holdout: relativedelta,
                      upper_cashout_boundary: float, lower_cashout_boundary: float):
    total_cashout = 0
    earnings = 0
    reference_value = 0
    reference_date = df.index[0] + max_holdout
    loses_cashout_dates = []
    profits_cashout_dates = []
    updated_reference = False

    for date in df.index:
        value = df.loc[date, 'value']
        if earnings >= minimum_cashout:
            if not updated_reference:
                reference_value = value
                updated_reference = True
            if value >= reference_value * (1 + upper_cashout_boundary) or date >= reference_date:
                total_cashout += (earnings * value) / (10 ** 6)
                earnings = 0
                updated_reference = False
                if value >= reference_value:
                    profits_cashout_dates.append(date)
                else:
                    loses_cashout_dates.append(date)

        if value <= reference_value * (1 - lower_cashout_boundary):
            total_cashout += (earnings * value) / (10 ** 6)
            earnings = 0
            updated_reference = False
            reference_value = value
            loses_cashout_dates.append(date)
        earnings += daily_earnings

    total_cashout += (earnings * value) / (10 ** 6)
    return total_cashout, profits_cashout_dates, loses_cashout_dates


def optimize_parameters(df: pd.DataFrame, initial_date: int, parameters: dict):
    initial_date = dt.datetime.strptime(str(initial_date), "%Y%m%d").date()
    df = df[df.date.dt.date >= initial_date]
    df.set_index('date', inplace=True)
    df.sort_index(ascending=True, inplace=True)

    simulation_results = pd.DataFrame()
    # i = 0
    for iteration_arguments in ParameterGrid(parameters):
        # i += 1
        # print(f'Starting iteration {i}')
        total_cashout, profits_cashout_dates, loses_cashout_dates = calculate_cashout(df, **iteration_arguments)

        results = iteration_arguments
        results.update({'total_cashout': total_cashout,
                        'profits_cashout_dates': profits_cashout_dates,
                        'loses_cashout_dates': loses_cashout_dates})
        results = {k: [v] for k, v in results.items()}
        simulation_results = simulation_results.append(pd.DataFrame(data=results, index=[0]),
                                                       ignore_index=True,
                                                       sort=False)
    simulation_results.sort_values('total_cashout', ascending=False, inplace=True)
    # option_context('display.max_rows', None)
    with option_context('display.max_columns', None), \
            option_context('expand_frame_repr', False):
        print('Best results:')
        print(simulation_results)

    best_results = simulation_results.iloc[0]
    plot_simulation_results(df, best_results)

    return best_results


def plot_simulation_results(df: pd.DataFrame, best_results: pd.Series):
    plt.plot(df.index, df.value)
    for date in best_results['loses_cashout_dates']:
        plt.axvline(x=date, color='red')
    for date in best_results['profits_cashout_dates']:
        plt.axvline(x=date, color='green')
    plt.show()


df = pd.read_csv('data/bitcoin_value.csv', parse_dates=[1])
df = df[['Date', '24h Low (USD)']]
df.columns = ['date', 'value']
# df['date'] = pd.to_datetime(df.date, infer_datetime_format=True).dt.date

parameters = {'daily_earnings': [50.0],
              'minimum_cashout': [300],
              'max_holdout': [relativedelta(months=3)],
              'upper_cashout_boundary': np.arange(0, 51, 1) / 100,
              'lower_cashout_boundary': np.arange(0, 51, 1) / 100}

best_results = optimize_parameters(df, 20160101, parameters)
print([str(date) for date in best_results['profits_cashout_dates']])

print('The end')
