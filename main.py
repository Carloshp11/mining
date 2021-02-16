import pandas as pd
import numpy as np
import datetime as dt
from matplotlib import pyplot as plt

from sklearn.model_selection import ParameterGrid


def calculate_cashout(df: pd.DataFrame, daily_earnings: float, minimum_cashout: int, initial_date: int,
                      upper_cashout_boundary: float, lower_cashout_boundary: float):
    initial_date = dt.datetime.strptime(str(initial_date), "%Y%m%d").date()
    df = df[df.date >= initial_date]
    df.set_index('date', inplace=True)
    df.sort_index(ascending=True, inplace=True)

    total_cashout = 0
    earnings = 0
    reference_value = 10 ** 10
    loses_cashout_dates = []
    profits_cashout_dates = []

    for date in df.index:
        value = df.loc[date, 'value']
        if earnings >= minimum_cashout and reference_value * (1 + upper_cashout_boundary) >= value:
            total_cashout += earnings
            earnings = 0
            profits_cashout_dates.append(date)

        if reference_value * (1 - lower_cashout_boundary) <= value:
            total_cashout += earnings
            earnings = 0
            loses_cashout_dates.append(date)
        earnings += daily_earnings

    total_cashout += earnings
    return total_cashout, profits_cashout_dates, loses_cashout_dates


df = pd.read_csv('bitcoin_value.csv')
df = df[['Date', '24h Low (USD)']]
df.columns = ['date', 'value']
df['date'] = pd.to_datetime(df.date).dt.date

parameters = {'minimum_cashout': [300],
              'upper_cashout_boundary': np.arange(5, 31, 1),
              'lower_cashout_boundary': np.arange(5, 31, 1)}


def optimize_parameters(df: pd.DataFrame, parameters: dict):
    simulation_results = pd.DataFrame()
    for iteration_arguments in ParameterGrid(parameters):
        total_cashout, profits_cashout_dates, loses_cashout_dates = calculate_cashout(df, **iteration_arguments)

        results = iteration_arguments
        results.update({'total_cashout': total_cashout,
                        'profits_cashout_dates': profits_cashout_dates,
                        'loses_cashout_dates': loses_cashout_dates})
        simulation_results = simulation_results.append(pd.DataFrame(data=results, index=[0]),
                                                       ignore_index=True,
                                                       sort=False)
    simulation_results.sort_values('total_cashout', ascending=False)
    print('Best results:')
    print(simulation_results.head(5))
    return simulation_results.iloc[0]


def plot_simulation_results(df: pd.DataFrame, best_results: pd.Series):
    plt.plot(df.index, df.value)
    for date in best_results['loses_cashout_dates']:
        plt.axvline(x=date)
    plt.show()


print('The end')
