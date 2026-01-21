# import requests library
import requests
# import plotting library
import matplotlib
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

endpoint = 'https://apidatos.ree.es'

get_archives = '/en/datos/mercados/precios-mercados-tiempo-real'

headers = {'Accept': 'application/json',
           'Content-Type': 'application/json',
           'Host': 'apidatos.ree.es'}

start_date = datetime.now()
end_date = start_date + timedelta(hours=24)  # add one day to see prices for tomorrow
# transform into strings with a minute resolution
end_date = end_date.strftime('%Y-%m-%dT%H:%M')
start_date = start_date.strftime('%Y-%m-%dT%H:%M')

params = {'start_date': start_date, 'end_date': end_date, 'time_trunc': 'hour'}

response = requests.get(endpoint + get_archives, headers=headers, params=params)

status = response.status_code

# Check the status code
if status < 200:
    print('informational')
    # If the status code is 200, treat the information.
elif status >= 200 and status < 300:
    print('Connection is established')
    # okBehavior(response) # runs the function to get list of archives
    # accessing data by means of a json object
    data_json = response.json()
    pvpc_data = data_json['included'][0]
    spot_market_data = data_json['included'][1]

    pvpc_values = pvpc_data['attributes']['values']
    spot_values = spot_market_data['attributes']['values']

    prices = []
    times = []
    for data_point in spot_values:
        # print(time_period['value'])
        prices.append(data_point['value'])
        times.append(data_point['datetime'])
        print(f"Spot price at {data_point['datetime']} is {data_point['value']} €/MWh")

    # Convert each string to datetime object for plot
    times = [datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z") for date_str in times]
    matplotlib.rc('xtick', labelsize=15)
    matplotlib.rc('ytick', labelsize=15)
    plt.style.use('ggplot')

    plt.figure(figsize=(20, 10))
    plt.plot(times, prices, 'r', linewidth=1.5, marker='.')
    plt.title(f"Spot market prices", fontsize=20)
    plt.xlabel('Hour', fontsize=20)
    plt.ylabel('Price [€/MWh]', fontsize=20)
    plt.show()

elif status >= 300 and status < 400:
    print('redirection')
elif status >= 400 and status < 500:
    print('client error')
else:
    print('server error')