import os
import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template, jsonify
from reporter_telegram import init_background_task

app = Flask(__name__)

# Cache local simple para no saturar APIs
cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 300 # 5 minutos

def fetch_market_data():
    if time.time() - cache['timestamp'] < CACHE_TTL and cache['data']:
        return cache['data']
    
    # 1. Binance Top 20 Volumen (Solo USDT)
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5)
        tickers = resp.json()
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        top_20 = usdt_pairs[:20]
    except:
        top_20 = []

    # 2. Fear and Greed Index
    try:
        fng_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        fng_data = fng_resp.json()['data'][0]
    except:
        fng_data = {'value': '--', 'value_classification': 'Desconocido'}

    # 3. Noticias Crypto (Parsing XML limpio sin dependencias extra)
    news = []
    try:
        rss_resp = requests.get("https://cointelegraph.com/rss", timeout=5)
        root = ET.fromstring(rss_resp.content)
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            news.append({'title': title, 'link': link})
    except:
        pass

    data = {
        'top_20': top_20,
        'fng': fng_data,
        'news': news
    }
    
    cache['data'] = data
    cache['timestamp'] = time.time()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    return jsonify(fetch_market_data())

if __name__ == '__main__':
    # Inicia hilo del Telegram Bot y Alertas
    init_background_task()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
