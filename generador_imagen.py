import os
from PIL import Image, ImageDraw, ImageFont
import datetime

def generar_imagen(top_gainers, top_losers, fng_value, fng_class):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(18, 18, 20))
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 30)
        font_text = ImageFont.truetype("arial.ttf", 20)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Cabecera
    fecha_str = datetime.date.today().strftime("%Y-%m-%d")
    draw.text((40, 30), f"Nexora Market Update | {fecha_str}", fill=(255, 255, 255), font=font_title)
    
    # FNG
    color_fng = (100, 255, 100) if int(fng_value) > 50 else (255, 100, 100)
    draw.text((40, 80), f"Fear & Greed Index: {fng_value} / 100 ({fng_class})", fill=color_fng, font=font_title)
    
    # Linea separadora
    draw.line((40, 130, width-40, 130), fill=(50, 50, 50), width=2)
    
    # Gainers (Verde)
    draw.text((40, 160), "TOP 5 ALZAS (24H):", fill=(100, 255, 100), font=font_title)
    y = 220
    for coin in top_gainers:
        texto = f"{coin['symbol'].replace('USDT','')} : +{coin['priceChangePercent']}%"
        draw.text((40, y), texto, fill=(230, 230, 230), font=font_text)
        y += 40
        
    # Losers (Rojo)
    draw.text((400, 160), "TOP 5 BAJAS (24H):", fill=(255, 100, 100), font=font_title)
    y = 220
    for coin in top_losers:
        texto = f"{coin['symbol'].replace('USDT','')} : {coin['priceChangePercent']}%"
        draw.text((400, y), texto, fill=(230, 230, 230), font=font_text)
        y += 40
        
    # Watermark
    draw.text((width - 250, height - 40), "Nexora Quant Technologies", fill=(100, 100, 100), font=font_text)
    
    os.makedirs('tmp', exist_ok=True)
    filepath = "tmp/market_summary.png"
    img.save(filepath)
    return filepath
