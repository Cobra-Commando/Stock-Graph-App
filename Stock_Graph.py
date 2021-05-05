# Proof of concept PySimpleGUI implementation of yfinance stock analysis program.
# Special thanks to Aditya Oberai @ https://github.com/aoberai/stock-trading-bot.
# For code demo purposes only. Not a real investment tool. Please be responsible.

# try/catch install of Python modules needed for this program
try:
    import PySimpleGUI as sg
    import yfinance as yf
    import matplotlib.pyplot as plt
    import math

except ImportError:
    import subprocess
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'PySimpleGUI==4.40.0'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'yfinance==0.1.59'])
    subprocess.check_call(["python3", '-m', 'pip', 'install', 'matplotlib==3.4.1'])
    import PySimpleGUI as sg
    import yfinance as yf
    import matplotlib.pyplot as plt
    import math

# PySimpleGUI theme choice
sg.theme('BluePurple')

# Dropdown choices for stocks
choices = ("AAPL", "INTC", "AMD", "NVDA", "TSLA", "MSFT", "QCOM", "IBM", "NFLX", "ROKU")

# Main menu layout
layout = [  [sg.Text('Which stock would you like to look at?')],
            [sg.Listbox(choices, size=(15, len(choices)), key='-STOCK-')],
            [sg.Button('Ok')]  ]

#Top menu title bar
window = sg.Window('Stock_Graph', layout)


# @param ticker_symbol - str
# @param time_period - Valid Periods: 1d, 5d, 1mo,3mo,6mo,1y,2y,5y,10y,ytd,maxi
# @param time_interval - Valid Periods:`1m , 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
def get_historical_data(ticker_symbol: str, time_period: str, time_interval: str) -> yf.Ticker:
    return yf.Ticker(ticker_symbol).history(period=time_period, interval=time_interval)


# Warning: Volume parameter from yfinance consistently yields zero.
def get_current_stock_data(ticker_symbol: str) -> {}:
    historical_stock_data = get_historical_data(ticker_symbol, '3d', '2m')
    stock_data = historical_stock_data.iloc[-1].to_dict()

    del stock_data['Dividends']
    del stock_data['Stock Splits']

    stock_data['SMA'] = calculate_sma(historical_stock_data)[0]  # method broken because of history access
    stock_data['PREVSMA'] = calculate_sma(historical_stock_data)[1]
    stock_data['EMA'] = calculate_ema(historical_stock_data)
    stock_data['PREVPRICE'] = historical_stock_data.iloc[-2].to_dict()[
        'Close']  # might need to change, only checks price 2 minutes ago

    return stock_data

# Do not refractor; creates price slope
def get_price_slope(ticker_symbol: str):
    n = 5  # checks last 3 minutes of data
    historical_stock_data = get_historical_data(ticker_symbol, '1d', '1m')
    stock_price_by_time = []
    for i in range(-n, 0):
        stock_price_by_time.append(historical_stock_data.iloc[i].to_dict()['Close'])
    slope = linear_regress_slope(1, stock_price_by_time)
    return slope

# Basic Math Functions
# param history : pd.DataFrame
# Return format: [current_sma, previous_sma]
def calculate_sma(history) -> []:
    summation = 0
    for row in history.iterrows():
        summation += row[1]['Close']
    return [summation/len(history.index), (summation - history.iloc[-2]['Close'])/(len(history.index)-1)]

# param history : pd.DataFrame
def calculate_ema(history) -> int:
    sma = calculate_sma(history)
    weighted_multiplier = 2 / (len(history.index) + 1)
    return history.iloc[-1]['Close']  * weighted_multiplier + sma[1] * (1 - weighted_multiplier)

def partition_array(array, number_of_partitions):
    partition_size = math.ceil(len(array)/number_of_partitions)
    chunked = []
    for i in range(number_of_partitions):
        if len(array) != 0:
            chunked.append(array[0:partition_size])
            del array[0:partition_size]
    return chunked

def calculate_price_change(final_price:int, original_price:int):
    return (final_price - original_price)/original_price

def check_overlap(phrase, sentence):
    if phrase !=  None and sentence != None:
        phrase_partitioned = phrase.split()

        for phrase in phrase_partitioned:
            for i in range(len(sentence) - 2):
                if len(phrase[i:i+3]) != 3:
                    break
                if phrase[i:i+3] in sentence:
                    return True

    return False

def linear_regress_slope(x_step, y_values):
    try:
        x_mean = (len(y_values)-1)/2
        y_mean = sum(y_values)/len(y_values)
        x_summation_stdev = 0
        y_summation_stdev = 0
        for i in range(0, len(y_values)):
            x_summation_stdev += (i - x_mean)**2
        for i in range(0, len(y_values)):
            y_summation_stdev += (y_values[i] - y_mean)**2

        x_std = (x_summation_stdev/(len(y_values)-1))**0.5
        y_std = (y_summation_stdev/(len(y_values)-1))**0.5

        summation_temp = 0
        for i in range(0, len(y_values)):
            summation_temp += ((i - x_mean)/x_std)*((y_values[i] - y_mean)/y_std)
        correlation_coefficent = summation_temp/(len(y_values) - 1)
        slope = correlation_coefficent * y_std/x_std
        return slope
    except Exception as e:
        return 0
# End of Basic Math Functions

# Event for matplotlib choice in main process window
def get_volume_slope(ticker_symbol: str):  # refactor maybe
    n = 5  # checks last 3 minutes of data
    historical_stock_data = get_historical_data(ticker_symbol, '1d', '1m')
    stock_volume_by_time = []
    for i in range(-n, 0):
        stock_volume_by_time.append(historical_stock_data.iloc[i].to_dict()['Volume'])
    slope = linear_regress_slope(1, stock_volume_by_time)
    return slope

# retrieves stock name for use with yfinance module
def get_stock_company_name(ticker_symbol: str):
    return yf.Ticker(ticker_symbol).info['longName']

# Method draws the actual stock price plot
def draw_plot(ticker: str):
    stock_prices = []
    n = 180
    for i in range(-n, 0, 1):
        stock_prices.append(get_historical_data(ticker, "1d", "1m").iloc[i].to_dict()['Volume'])
    plt.plot(list(range(n)), stock_prices, 'xb-')
    plt.show(block=False)

# Main output window displays the console data and fires off matplotlib graph
while True:                  # the PySimpleGUI main event loop
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Cancel'):
        break
    if event == 'Ok':
        if values['-STOCK-']:    # if something is highlighted in the list
            sg.Print('Setting up data-scan...', do_not_reroute_stdout=False)
            print(f"You have chosen {values['-STOCK-'][0]}")
            # matplotlib method call
            stock = str(values['-STOCK-'][0])
            draw_plot(stock)
            # subsequent stock data displayed for debugging purposes
            value_alpha = get_volume_slope(str(stock))
            print("Current volume slope: " + str(value_alpha))
            value_zeta = get_current_stock_data(str(stock))
            print("Current stock data: " + str(value_zeta))
window.close()