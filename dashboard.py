from flask import Flask, render_template_string
import requests

app = Flask(__name__)

# Replace with your OpenWeather API key
OPENWEATHER_API_KEY = "5d86584e0d3835ed219609c81c15faf6"
CITY = "Crowley"

# CoinGecko API endpoint
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"

@app.route('/')
def dashboard():
    # Get weather data
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&units=imperial&appid={OPENWEATHER_API_KEY}"
    weather_response = requests.get(weather_url).json()
    print("DEBUG weather_response:", weather_response)

    temp = weather_response['main']['temp']
    desc = weather_response['weather'][0]['description']

    # Get crypto prices
    crypto_response = requests.get(COINGECKO_URL).json()
    btc_price = crypto_response['bitcoin']['usd']
    eth_price = crypto_response['ethereum']['usd']

    html = f"""
    <h1>Personal Dashboard</h1>
    <h2>Weather in {CITY}</h2>
    <p>Temperature: {temp}°F</p>
    <p>Description: {desc}</p>
    <h2>Crypto Prices</h2>
    <p>Bitcoin: ${btc_price}</p>
    <p>Ethereum: ${eth_price}</p>
    """

    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
