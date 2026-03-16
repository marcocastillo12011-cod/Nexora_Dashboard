import os
import time
import threading
import datetime
import requests
from generador_imagen import generar_imagen

# Historial para detectar anomalias (movimientos rapidos > 5%)
history_1h = {}
last_1h_update = time.time()
last_report_hour = -1

def get_binance_data():
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        return [t for t in resp.json() if t['symbol'].endswith('USDT')]
    except:
        return []

def run_scheduler():
    global last_1h_update, last_report_hour
    
    while True:
        now = datetime.datetime.utcnow()
        
        # 1. Reportes programados
        horas_str = os.environ.get('REPORT_HOURS', '8,14,20').split(',')
        report_hours = [int(h.strip()) for h in horas_str if h.strip()]
        
        if now.hour in report_hours and now.minute == 0 and last_report_hour != now.hour:
            send_daily_report()
            last_report_hour = now.hour
            
        # 2. Monitoreo de anomalias (Actualiza snapshot cada 1 hora)
        if time.time() - last_1h_update > 3600:
            update_history()
            last_1h_update = time.time()
        else:
            check_unusual_movements()
            
        time.sleep(60)

def update_history():
    global history_1h
    data = get_binance_data()
    for d in data:
        history_1h[d['symbol']] = float(d['lastPrice'])

def check_unusual_movements():
    token = os.environ.get('TELEGRAM_TOKEN_DASHBOARD')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID')
    if not token or not chat_id: return
    if not history_1h: return
    
    data = get_binance_data()
    for d in data:
        sym = d['symbol']
        current = float(d['lastPrice'])
        if sym in history_1h:
            old = history_1h[sym]
            if old > 0:
                change = ((current - old) / old) * 100
                if abs(change) >= 5.0:
                    direccion = "SUBIDO" if change > 0 else "BAJADO"
                    msg = (
                        f"[ALERTA INUSUAL DE MERCADO]\n\n"
                        f"{sym} ha {direccion} {abs(change):.2f}% en la ultima hora.\n"
                        f"Precio actual: ${current}\n\n"
                        f"#Volatilidad #CryptoAlerta"
                    )
                    try:
                        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': msg})
                    except:
                        pass
                    # Resetear para no spamear
                    history_1h[sym] = current

def send_daily_report():
    token = os.environ.get('TELEGRAM_TOKEN_DASHBOARD')
    chat_id = os.environ.get('TELEGRAM_CHANNEL_ID')
    if not token or not chat_id: return
    
    data = get_binance_data()
    if not data: return
    
    data.sort(key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_gainers = data[:5]
    top_losers = [d for d in data if float(d['priceChangePercent']) < 0][-5:]
    
    try:
        fng_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()['data'][0]
    except:
        fng_resp = {'value': '50', 'value_classification': 'Neutral'}
        
    img_path = generar_imagen(top_gainers, top_losers, fng_resp['value'], fng_resp['value_classification'])
    
    caption = (
        "Reporte de Mercado Nexora\n\n"
        f"FNG Index: {fng_resp['value']} - {fng_resp['value_classification']}\n\n"
        "Principales movimientos del mercado registrados en las ultimas 24 horas.\n"
        "#Criptomonedas #Mercado #Tendencias #Inversion"
    )
    
    try:
        with open(img_path, 'rb') as f:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={'chat_id': chat_id, 'caption': caption},
                files={'photo': f}
            )
    except Exception as e:
        print("Error Telegram:", e)

def init_background_task():
    update_history()
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
