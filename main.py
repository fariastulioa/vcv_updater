import functools
from typing import Any, Callable
from time import perf_counter
import logging
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import json
import sqlite3
import datetime
import re

"""
This is a Python script that gets current information about Vancouver and sends it to a telegram chat

It works by:
o stories
 - Getting the current temperature and humidity for Vancouver location from Google search
 - Getting today's exchange rate from Canadian Dolars to Brazilian Reals  
    
 - Connecting to a Telegram bot that sends the updated information to an user
    - the telegram API is accessed using the bot api token to establish connection to the bot
    - the bot can then send message to a chat with the user, using the specific chat ID

Telegram tasks are run asynchronously to ensure they have enough time to complete without errors and prevent errors
due to flood control. These are run with a short time interval between them
"""


# First, get constant values, tokens, api keys, etc.


# The token to connect to the Telegram bot API
bot_token = ""

# The ID the bot uses to send chat messages
bot_chat_id = ""

# Location to check the weather of
city = ""

# My location
location = ''

# My language
language = ''

# My user agent string
user_agent = ""

# Encode the query parameters
location_encoded = requests.utils.quote(location)
language_encoded = requests.utils.quote(language)


# This is a decorator to implement basic logging in any function for debugging
def log_it_dec(func: Callable[..., Any]) -> Callable[..., Any]:

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        
        logging.info(f"About to run {func.__name__} ...")
        output = func(*args, **kwargs)
        logging.info(f"Just ran {func.__name__} !")
        
        return(output)
    
    return(wrapper)

# This is a decorator to implement basic run time measurements in any function for debugging and performance analysis
def time_it_dec(func: Callable[..., Any]) -> Callable[..., Any]:
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        
        start_time = perf_counter()
        output = func(*args, **kwargs)
        end_time = perf_counter()
        
        run_time = end_time - start_time
        logging.info(f"Execution of {func.__name__} lasted {run_time:.2f} seconds.")
        
        return(output)
    return(wrapper)








@time_it_dec
@log_it_dec
def extract_value(fullstring):

    pattern = r"[\d\.]+"
    extracted_values = re.findall(pattern, str(fullstring))
    
    return("".join(extracted_values))



@time_it_dec
@log_it_dec
def get_temperature(city):
    """Checks temperature in that city
    
    Keyword arguments:
    city -- the city to check the weather for
    Return: the current temperature for that city
    """
    
    url = f"https://www.google.com/search?q={city}+temperature"
    response = requests.get(url)
    sopa = BeautifulSoup(response.text, 'html.parser')
    
    temperature = sopa.find('div', class_='BNeawe').text
    
    temperature = extract_value(temperature)

    return(float(temperature))


@time_it_dec
@log_it_dec
def get_humidity(city):
    """Checks humidity in that city
    
    Keyword arguments:
    city -- the city to check the weather for
    Return: the current humidity for that city
    """
    #url = f"https://www.google.com/search?q={city}+humidade"
    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, "html.parser")

    #humidity = soup.select_one('div.Ww4FFb div[data-vew-view] div.nawv0d div.UQt4rd div.wtsRwe span#wob_hm')
    
    headers = {'User-Agent': user_agent}
    city = "".join(city.split())
    url = f'https://www.google.com/search?q=vancouver+british+columbia+canada+humidade&hl={language_encoded}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    humidity_element = soup.find('span', {'id': 'wob_hm'})
    humidity = humidity_element.text.split(':')[-1].strip()
    
    
    # Extract the humidity value from the HTML response
    #humidity = soup.find("span", class_="r0bn4c rQMQod")
    print(humidity)
    humidity = extract_value(humidity)
    return (float(humidity))


@time_it_dec
@log_it_dec
def get_exchange_rate():
    """Gets current exchange rate from CAD to BRL
    
    Return: return a float representing the current exchange rate
    """
    
    url = "https://www.google.com/search?q=1+CAD+to+BRL"
    response = requests.get(url)
    sopa = BeautifulSoup(response.text, "html.parser")
    
    exchange_rate = sopa.find('div', class_='BNeawe iBp4i AP7Wnd').text
    exchange_rate = exchange_rate.replace(",", ".")
    exchange_rate = extract_value(exchange_rate)
    return(float(exchange_rate))






@time_it_dec
@log_it_dec
def get_bot(api_token):
    """
    This instanciates a bot object using Telegram library and the access token to the specific bot API
    """
    bot = telegram.Bot(token=api_token)
    return(bot)


@time_it_dec
@log_it_dec
async def message_telegram(bot, temperature, humidity, cad_price):
    """
    This function uses the weather data to send a custom updated message to a Telegram user through the bot
    Keyword arguments:
    bot -- the Telegram bot object
    temperature -- the temperature checked using google
    humidity -- the humidity checked using google
    cad_price -- the exchange rate checked using google
    """

    messages = [] 
    
    messages.append(f"Current Temperature in Vancouver: {temperature} °C")
    messages.append(f"Current Humidity in Vancouver: {humidity} %")
    messages.append(f"Today's CAD price in Reais: {cad_price}")
    
    try:
        for message in messages:
            await asyncio.sleep(2)
            await bot.send_message(chat_id=bot_chat_id, text=message)
            await asyncio.sleep(2)
    except telegram.error.RetryAfter as e:
        retry_seconds = e.retry_after
        print(f"Flood control exceeded. Retry after {retry_seconds} seconds.")
        await bot.close()
        await asyncio.sleep(retry_seconds)
        
        await message_telegram(bot)
    finally:
        return(temperature, humidity)




@time_it_dec
@log_it_dec
async def save_today_data(brl_rate, temperature, humidity):
    
    date = datetime.date.today().strftime("%Y%m%d")
    # Connect to the SQLite database
    with sqlite3.connect('vancouver_database.db') as conn:
        cursor = conn.cursor()

        # Insert the new row into the table
        cursor.execute(r"""INSERT INTO daily_vancouver (date, brl_rate, temperature, humidity) VALUES (?, ?, ?, ?)""",
                    (date, brl_rate, temperature, humidity))

        # Commit the changes to the database
        conn.commit()
        cursor.close()


        

async def main():
    """
    Main function used to run the script in a logically organized way
    """
    
    
    temperature = get_temperature(city)
    humidity = get_humidity(city)
    exchange_rate = get_exchange_rate()

    
    
    
    bot = get_bot(api_token=bot_token)


    await save_today_data(float(exchange_rate), float(temperature), float(humidity))
    
    await asyncio.sleep(1)
    
    await message_telegram(bot, temperature, humidity, exchange_rate)
    await asyncio.sleep(1)
    

    
    await bot.close()

    return()


# Main script body
if __name__ == "__main__":
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

    loop.close()

    