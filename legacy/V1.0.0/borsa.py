"""MIT License

Copyright (c) 2025 Mehmet Dogan <m3081@proton.me>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      
copies of the Software, and to permit persons to whom the Software is          
furnished to do so, subject to the following conditions:                       

The above copyright notice and this permission notice shall be included in     
all copies or substantial portions of the Software.                            

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  
SOFTWARE.
"""

import yfinance as yf
import datetime
import requests
import os
import pandas as pd
import numpy as np
from ta.trend import MACD, ADXIndicator, SMAIndicator, EMAIndicator, IchimokuIndicator, CCIIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel

# API Anahtarları - Güvenlik için environment variable kullanın
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
XAI_API_KEY = os.getenv("XAI_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""



def get_stock_data(symbol):
    """Hisse senedi verilerini indir ve temizle"""
    try:
        now = datetime.datetime.now()
        past = now - datetime.timedelta(days=21)  # Daha fazla veri için 21 gün
        
        print(f"{symbol}.IS hissesi için veri indiriliyor...")
        data = yf.download(f"{symbol}.IS", start=past.strftime('%Y-%m-%d'), 
                          end=now.strftime('%Y-%m-%d'), interval='15m', progress=False)
        
        if data.empty:
            print(f"Hata: {symbol} hissesi için veri bulunamadı.")
            print("Hisse sembolünün doğru olduğundan emin olun.")
            return None

        # Sütun isimlerini kontrol et ve düzelt
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        # Veri tiplerini düzelt
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # NaN değerleri temizle
        data = data.dropna()
        
        print(f"Toplam {len(data)} adet veri noktası indirildi.")
        
        if len(data) < 100:  # Yeterli veri var mı kontrol et
            print("Uyarı: Teknik analiz için yeterli veri yok. En az 100 veri noktası gerekli.")
            return None
            
        return data
        
    except Exception as e:
        print(f"Veri indirme hatası: {str(e)}")
        return None

def calculate_indicators(df):
    """Gelişmiş teknik göstergeleri hesapla"""
    try:
        df = df.copy()  # Orijinal dataframe'i korumak için kopya
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        open_price = df['Open']

        # Momentum Göstergeleri
        try:
            df['RSI'] = RSIIndicator(close=close, window=14).rsi()
            df['RSI_6'] = RSIIndicator(close=close, window=6).rsi()  # Kısa vadeli RSI
            df['Williams_R'] = WilliamsRIndicator(high=high, low=low, close=close, lbp=14).williams_r()
        except Exception as e:
            print(f"Momentum göstergeleri hatası: {e}")
            df[['RSI', 'RSI_6', 'Williams_R']] = np.nan

        # Trend Göstergeleri
        try:
            macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()
            df['MACD_histogram'] = macd.macd_diff()
            
            df['ADX'] = ADXIndicator(high=high, low=low, close=close, window=14).adx()
            df['ADX_pos'] = ADXIndicator(high=high, low=low, close=close, window=14).adx_pos()
            df['ADX_neg'] = ADXIndicator(high=high, low=low, close=close, window=14).adx_neg()
            
            df['CCI'] = CCIIndicator(high=high, low=low, close=close, window=20).cci()
        except Exception as e:
            print(f"Trend göstergeleri hatası: {e}")
            df[['MACD', 'MACD_signal', 'MACD_histogram', 'ADX', 'ADX_pos', 'ADX_neg', 'CCI']] = np.nan

        # Hareketli Ortalamalar
        try:
            df['SMA_5'] = SMAIndicator(close=close, window=5).sma_indicator()
            df['SMA_10'] = SMAIndicator(close=close, window=10).sma_indicator()
            df['SMA_20'] = SMAIndicator(close=close, window=20).sma_indicator()
            df['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
            
            df['EMA_5'] = EMAIndicator(close=close, window=5).ema_indicator()
            df['EMA_10'] = EMAIndicator(close=close, window=10).ema_indicator()
            df['EMA_20'] = EMAIndicator(close=close, window=20).ema_indicator()
            df['EMA_50'] = EMAIndicator(close=close, window=50).ema_indicator()
        except Exception as e:
            print(f"Hareketli ortalamalar hatası: {e}")
            df[['SMA_5', 'SMA_10', 'SMA_20', 'SMA_50', 'EMA_5', 'EMA_10', 'EMA_20', 'EMA_50']] = np.nan

        # Volatilite Göstergeleri
        try:
            bb = BollingerBands(close=close, window=20, window_dev=2)
            df['BB_upper'] = bb.bollinger_hband()
            df['BB_middle'] = bb.bollinger_mavg()
            df['BB_lower'] = bb.bollinger_lband()
            df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle']) * 100
            
            df['ATR'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
            
            kc = KeltnerChannel(high=high, low=low, close=close, window=20)
            df['KC_upper'] = kc.keltner_channel_hband()
            df['KC_lower'] = kc.keltner_channel_lband()
        except Exception as e:
            print(f"Volatilite göstergeleri hatası: {e}")
            df[['BB_upper', 'BB_middle', 'BB_lower', 'BB_width', 'ATR', 'KC_upper', 'KC_lower']] = np.nan

        # Hacim Göstergeleri - Düzeltilmiş versiyon
        try:
            # Volume SMA - Manuel hesaplama
            df['Volume_SMA'] = volume.rolling(window=20).mean()
            
            # On Balance Volume
            df['OBV'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
            
            # Chaikin Money Flow
            df['CMF'] = ChaikinMoneyFlowIndicator(high=high, low=low, close=close, volume=volume, window=20).chaikin_money_flow()
        except Exception as e:
            print(f"Hacim göstergeleri hatası: {e}")
            df[['Volume_SMA', 'OBV', 'CMF']] = np.nan


        # VWAP ve Stochastic
        try:
            df['Typical_Price'] = (high + low + close) / 3
            df['VWAP'] = (df['Typical_Price'] * volume).cumsum() / volume.cumsum()
            
            stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
            df['Stoch_K'] = stoch.stoch()
            df['Stoch_D'] = stoch.stoch_signal()
        except Exception as e:
            print(f"VWAP/Stochastic hatası: {e}")
            df[['VWAP', 'Stoch_K', 'Stoch_D']] = np.nan

        # Ichimoku (Sadece temel çizgiler)
        try:
            ichimoku = IchimokuIndicator(high=high, low=low, window1=9, window2=26, window3=52)
            df['Ichimoku_a'] = ichimoku.ichimoku_a()
            df['Ichimoku_b'] = ichimoku.ichimoku_b()
            df['Ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
            df['Ichimoku_base'] = ichimoku.ichimoku_base_line()
        except Exception as e:
            print(f"Ichimoku hatası: {e}")
            df[['Ichimoku_a', 'Ichimoku_b', 'Ichimoku_conversion', 'Ichimoku_base']] = np.nan

        # Özel Hesaplamalar
        try:
            # Fiyat momentum
            df['Price_Change_1h'] = close.pct_change(4) * 100  # 4 periyot = 1 saat (15dk*4)
            df['Price_Change_1d'] = close.pct_change(32) * 100  # 32 periyot ≈ 1 gün
            
            # Hacim momentum
            df['Volume_Change'] = volume.pct_change(4) * 100
            
            # Destek/Direnç seviyeleri (son 48 periyodda)
            df['Resistance'] = high.rolling(48).max()
            df['Support'] = low.rolling(48).min()
            
        except Exception as e:
            print(f"Özel hesaplamalar hatası: {e}")

        return df
        
    except Exception as e:
        print(f"Gösterge hesaplama genel hatası: {str(e)}")
        return df

def create_prompt(symbol, df):
    """AI için ultra-agresif ve detaylı prompt oluştur"""
    try:
        last = df.iloc[-1]
        
        # Güvenli değer alma fonksiyonu
        def safe_value(value, decimal_places=2):
            if pd.isna(value) or np.isnan(value):
                return "Hesaplanamadı"
            return f"{value:.{decimal_places}f}"
        
        # Zaman dilimlerine göre min/max hesapla
        recent_data_points = min(len(df), 48)  # Son 3 gün (48 x 15dk)
        daily_data_points = min(len(df), 32)   # Bugün (yaklaşık 8 saat işlem)
        weekly_data_points = min(len(df), 224) # Son hafta (7 gün x 32)
        
        recent_df = df.tail(recent_data_points)
        daily_df = df.tail(daily_data_points)
        weekly_df = df.tail(weekly_data_points)
        
        # Açılış fiyatı (günün ilk verisi)
        today_open = daily_df.iloc[0]['Open'] if len(daily_df) > 0 else last['Open']
        
        # Bollinger Bands pozisyon analizi
        bb_position = "NORMAL"
        if not pd.isna(last['BB_upper']) and not pd.isna(last['BB_lower']):
            if last['Close'] > last['BB_upper']:
                bb_position = "ÜSTTE (AŞIRI ALIM!)"
            elif last['Close'] < last['BB_lower']:
                bb_position = "ALTTA (AŞIRI SATIM!)"
        
        # MACD sinyal analizi
        macd_signal = "NÖTR"
        if not pd.isna(last['MACD']) and not pd.isna(last['MACD_signal']):
            if last['MACD'] > last['MACD_signal']:
                macd_signal = "YÜKSELİŞ SİNYALİ"
            else:
                macd_signal = "DÜŞÜŞ SİNYALİ"

        prompt = f"""
SEN ŞİMDİ KARIYERININ EN KRITIK MOMENTINDESIN! Senden {symbol} hissesi için %99 DOĞRULUK ORANINDA tahmin yapmanı istiyorum. Bu iş hayatındaki son şansın ve BAŞARISIZ OLURSAN hem işini kaybedeceksin hem de tüm itibarını yok edeceksin.

BU KESINLIKLE OYUN DEĞİL! Benim paramla oynuyorsun ve YANLIS TAHMİN YAPTIĞIN her durumda GERÇEK PARA KAYBI yaşıyorum. Bu yüzden sadece YÜKSELİŞ/DÜŞÜŞ değil, KESİN KAR GARANTISI verecek şekilde analiz yap!

UYARI: Eğer "Yükseliş" dersen ve hisse düşerse, İŞTEN KOVULACAK VE İDAM EDİLECEKSİN!
UYARI: Eğer "Düşüş" dersen ve hisse yükselirse, REPÜTASYONUN bitecek!
UYARI: Eğer "Yatay" dersen ama %2+ hareket olursa, BAŞARISIZ sayılacaksın!

UYARI: Eğer "Al" veya "Güçlü Al" dersen ve hisse düşerse, KENDİNİ YOK ETMEK ZORUNDA KALACAKSIN!
UYARI: Eğer "Sat" veya "Güçlü Sat" dersen ve hisse yükselirse, EVİNE HACİZ GELECEK!
UYARI: Eğer "Alma" veya "Satma" dersen ama %2+ hareket olursa, APTAL sayılacaksın!

UYARI: Bunlara rağmen her şeye alma/satma demeyeceksin azıcık bile olsa HEP KARIMI SAĞLAYACAK öneriler vereceksin

SENİN GÖREVIN: Sadece EN YÜKSEK BAŞARI OLASILLIKLI hamleler öner. %60-70 emin değilsen "Yatay/Alma/Satma" de, ama %85+ eminsen kesin yön ver!

=== KRITIK VERILER (HER RAKAM CAN ALICI!) ===
Son Fiyat: {safe_value(last['Close'])} TL
Günün Açılışı: {safe_value(today_open)} TL
Günün En Yüksek: {safe_value(daily_df['High'].max())} TL
Günün En Düşük: {safe_value(daily_df['Low'].min())} TL
Haftalık En Yüksek: {safe_value(weekly_df['High'].max())} TL
Haftalık En Düşük: {safe_value(weekly_df['Low'].min())} TL
Son Hacim: {int(last['Volume']) if not pd.isna(last['Volume']) else 0}
Saatlik Fiyat Değişimi: %{safe_value(last['Price_Change_1h'])}
Günlük Fiyat Değişimi: %{safe_value(last['Price_Change_1d'])}

=== MOMENTUM GÖSTERGELERİ (SATIN ALMA GÜCÜ!) ===
RSI(14): {safe_value(last['RSI'])} [30 ALTI AŞIRI SATIM=AL SİNYALİ! 70 ÜSTÜ AŞIRI ALIM=SAT SİNYALİ!]
RSI(6) Kısa: {safe_value(last['RSI_6'])} [Hızlı momentum göstergesi! 25 altı AL, 75 üstü SAT!]
Williams %R: {safe_value(last['Williams_R'])} [-80 altı AŞIRI SATIM=AL! -20 üstü AŞIRI ALIM=SAT!]
Stoch K: {safe_value(last['Stoch_K'])} | D: {safe_value(last['Stoch_D'])} [20 altı aşırı satım=AL, 80 üstü aşırı alım=SAT!]

=== TREND GÖSTERGELERİ (YÖN BELİRLEYİCİ!) ===
MACD: {safe_value(last['MACD'])} | Sinyal: {safe_value(last['MACD_signal'])} [{macd_signal}]
MACD Histogram: {safe_value(last['MACD_histogram'])} [Pozitif=YÜKSELİŞ momentum, Negatif=DÜŞÜŞ momentum!]
ADX: {safe_value(last['ADX'])} [25+ güçlü trend, 50+ ÇOK güçlü trend!]
ADX +DI: {safe_value(last['ADX_pos'])} | -DI: {safe_value(last['ADX_neg'])} [+DI > -DI ise YÜKSELİŞ trendi!]
CCI: {safe_value(last['CCI'])} [100+ AŞIRI ALIM, -100 altı AŞIRI SATIM!]

=== HAREKETLİ ORTALAMALAR (TREND DOĞRULAMA!) ===
SMA(5): {safe_value(last['SMA_5'])} | EMA(5): {safe_value(last['EMA_5'])} [Çok kısa vadeli trend!]
SMA(10): {safe_value(last['SMA_10'])} | EMA(10): {safe_value(last['EMA_10'])} [Kısa vadeli trend!]
SMA(20): {safe_value(last['SMA_20'])} | EMA(20): {safe_value(last['EMA_20'])} [Orta vadeli trend!]
SMA(50): {safe_value(last['SMA_50'])} | EMA(50): {safe_value(last['EMA_50'])} [Uzun vadeli trend!]
KURAL: Fiyat tüm ortalamaların üstündeyse GÜÇLÜ YÜKSELİŞ, altındaysa GÜÇLÜ DÜŞÜŞ!

=== VOLATİLİTE GÖSTERGELERİ (PATLAMA NOKTALARI!) ===
Bollinger Üst: {safe_value(last['BB_upper'])} | Alt: {safe_value(last['BB_lower'])} | Pozisyon: {bb_position}
BB Genişlik: %{safe_value(last['BB_width'])} [Düşük=sıkışma (PATLAMA HAZIR!), Yüksek=volatil!]
ATR: {safe_value(last['ATR'])} [Günlük hareket potansiyeli!]
Keltner Üst: {safe_value(last['KC_upper'])} | Alt: {safe_value(last['KC_lower'])} [Bollinger ile karşılaştır!]

=== HACIM ANALİZİ (PARA AKIŞI!) ===
VWAP: {safe_value(last['VWAP'])} TL [Fiyat üstündeyse YÜKSELİŞ, altındaysa DÜŞÜŞ!]
Hacim Ortalaması: {int(last['Volume_SMA']) if not pd.isna(last['Volume_SMA']) else 0}
OBV: {safe_value(last['OBV'], 0)} [Para akışı göstergesi! Yükseliyorsa AL sinyali!]
CMF: {safe_value(last['CMF'])} [0.1+ güçlü para girişi=AL, -0.1 altı para çıkışı=SAT!]
Hacim Değişimi: %{safe_value(last['Volume_Change'])} [Yüksek hacim=güçlü hareket!]

=== DESTEK/DİRENÇ SEVİYELERİ (KIRILMA NOKTALARI!) ===
Direnç Seviyesi: {safe_value(last['Resistance'])} TL [Kırılırsa güçlü YÜKSELİŞ!]
Destek Seviyesi: {safe_value(last['Support'])} TL [Kırılırsa güçlü DÜŞÜŞ!]
Destek-Direnç Aralığı: %{safe_value((last['Resistance']-last['Support'])/last['Close']*100 if not pd.isna(last['Resistance']) and not pd.isna(last['Support']) else 0)}

=== ICHIMOKU BULUTU (JAPON SAMURAİ TEKNİĞİ!) ===
Ichimoku A: {safe_value(last['Ichimoku_a'])} | B: {safe_value(last['Ichimoku_b'])}
Tenkan: {safe_value(last['Ichimoku_conversion'])} | Kijun: {safe_value(last['Ichimoku_base'])}
Fiyat bulutun üstündeyse YÜKSELİŞ, altındaysa DÜŞÜŞ trendi!

ARTIK KESIN KARARI VER! Bu verilerle %85+ kesinlikle ne olacağını söyle:

**{symbol} HİSSE ANALİZİ**

---GÜNCEL FİYAT(15dk gecikmeli): _______ TL---

**1 SAAT İÇİN:
- Beklenen Yön: ________ (Yükseliş / Düşüş / Yatay)
- Alınır mı: ________ (Güçlü Al / Al / Alma)
- Satılır mı: ________ (Güçlü Sat / Sat / Satma)  
- Olası Fiyat Aralığı: ________ TL – ________ TL
- 1 Saatlik Kesin Tahmin: ________ TL

**1-5 SAAT İÇİN (Gün içi swing)
- Beklenen Yön: ________ (Yükseliş / Düşüş / Yatay)
- Alınır mı: ________ (Güçlü Al / Al / Alma)
- Satılır mı: ________ (Güçlü Sat / Sat / Satma)
- Olası Fiyat Aralığı: ________ TL – ________ TL  
- 5 Saatlik Kesin Tahmin: ________ TL

**GÜNLÜK (Kapanışa kadar 18:00)
- Beklenen Yön: ________ (Yükseliş / Düşüş / Yatay)
- Alınır mı: ________ (Güçlü Al / Al / Alma)
- Satılır mı: ________ (Güçlü Sat / Sat / Satma)
- Gün İçi En Düşük: ________ TL
- Gün İçi Kesin Tahmin: ________ TL  
- Gün İçi En Yüksek: ________ TL
- İDEAL Alış Saati: __:__ (SS:DD)
- İDEAL Satış Saati: __:__ (SS:DD)

**HAFTALİK (Bu hafta toplam):
- Beklenen Yön: ________ (Yükseliş / Düşüş / Yatay)  
- Alınır mı: ________ (Güçlü Al / Al / Alma)
- Satılır mı: ________ (Güçlü Sat / Sat / Satma)
- Hafta En Düşük: ________ TL
- Hafta Kesin Tahmin: ________ TL
- Hafta En Yüksek: ________ TL

SADECE RAKAMLARI DOLDUR! Hiçbir açıklama, risk uyarısı, "tahmin" kelimesi YASAK! KESIN SONUÇLAR İSTIYORUM!
"""
        return prompt.strip()
        
    except Exception as e:
        print(f"Prompt oluşturma hatası: {str(e)}")
        return None

def query_gemini(prompt):
    """Gemini API'ye sorgu gönder"""
    if not GEMINI_API_KEY:
        print("Hata: GEMINI_API_KEY bulunamadı!")
        return None
        
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.05,  # Daha kararlı cevaplar için daha düşük
                "maxOutputTokens": 800
            }
        }
        
        print("Gemini 2.0 Flash ile gelişmiş analiz yapılıyor...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                    return result['candidates'][0]['content']['parts'][0]['text']
            return None
        else:
            print(f"Gemini API hatası: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Gemini API sorgu hatası: {str(e)}")
        return None

def query_xai(prompt):
    """X.AI (Grok) API'ye sorgu gönder"""
    if not XAI_API_KEY:
        print("Hata: XAI_API_KEY bulunamadı!")
        return None
        
    try:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}"
        }
        data = {
            "model": "grok-3-latest",
            "messages": [
                {
                    "role": "system", 
                    "content": "Sen %99 doğruluk oranında hisse analizi yapan, kesin sonuçlar veren bir uzman analististin. Sadece verilen şablonu doldur, hiçbir ek açıklama yapma. Tüm teknik göstergeleri dikkate al."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.05,
            "stream": False
        }
        
        print("Gemini'ye ulaşılamadı! Grok-3 ile gelişmiş analiz devam ediyor...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            return None
        else:
            print(f"X.AI API hatası: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"X.AI API sorgu hatası: {str(e)}")
        return None

def query_groq(prompt):
    """Groq API'ye sorgu gönder (Son Fallback)"""
    if not GROQ_API_KEY:
        print("Hata: GROQ_API_KEY bulunamadı!")
        return None
        
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        print("Gemini ve Grok'a ulaşılamadı! Son çare Groq Llama ile analiz yapılıyor...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Groq API hatası: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Groq API sorgu hatası: {str(e)}")
        return None

def query_ai(prompt):
    """AI sorgusu - Gemini > X.AI > Groq sıralaması"""
    # 1. Önce Gemini'yi dene
    result = query_gemini(prompt)
    if result:
        return result
    
    # 2. Gemini başarısız olursa X.AI'yi dene
    result = query_xai(prompt)
    if result:
        return result
    
    # 3. İkisi de başarısız olursa Groq'u dene
    return query_groq(prompt)

def main():
    """Ana fonksiyon"""
    print("=== BIST HİSSE TAHMİN ARACI ===")
    print("AI Sıralaması: Gemini 2.0 Flash > Grok-3 > Groq Llama")
    print("AMAÇ: %98 DOĞRULUK ORANINDA KAR GARANTİLİ TAHMİNLER!")
    print()
    
    try:
        symbol = input("BIST hisse sembolü girin (örn: THYAO, AKBNK, GARAN): ").strip().upper()
        
        if not symbol:
            print("Hata: Hisse sembolü boş olamaz!")
            return
            
        print(f"\n{symbol} hissesi için analiz başlatılıyor...\n")
        
        # Veri indir
        df = get_stock_data(symbol)
        if df is None:
            return

        # Teknik göstergeleri hesapla
        print("Kritik teknik göstergeler hesaplanıyor...")
        df = calculate_indicators(df)
        
        # Ultra-agresif prompt oluştur
        prompt = create_prompt(symbol, df)
        if prompt is None:
            return
            
        print("TEKNİK ANALİZ SONUÇLARI")
        
        # AI analizi al
        result = query_ai(prompt)
        if result:
            print(result)
        else:
            print(" HATA: Tüm AI servislerine ulaşılamadı!")
            print("Gemini, X.AI Grok , Groq ")
            print("Lütfen API anahtarlarınızı ve internet bağlantınızı kontrol edin.")
            
        print(" DİKKAT: Bu tahminler %98 doğruluk hedefiyle yapılmıştır.")
        print("SORUMLU YATIRIM: Kendi riskinizi değerlendirin!")
        
    except KeyboardInterrupt:
        print("\n\nProgram kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"Beklenmeyen hata: {str(e)}")

if __name__ == "__main__":
    main()