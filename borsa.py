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

# API Anahtarları
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY") or ""
XAI_API_KEY = os.getenv("XAI_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""

def is_market_open():
    """BIST'in açık olup olmadığını kontrol eder"""
    try:
        # Türkiye saatini al
        turkey_tz = datetime.timezone(datetime.timedelta(hours=3))
        now = datetime.datetime.now(turkey_tz)
        
        # Hafta sonları kontrolü
        if now.weekday() >= 5:  # Cumartesi (5) ve Pazar (6)
            return False, f"Hafta sonu - BIST kapalı (Bugün: {get_day_name(now.weekday())})"
        
        # Resmi tatil kontrolü
        is_holiday, holiday_name = is_national_holiday(now.date())
        if is_holiday:
            return False, f"Resmi tatil - BIST kapalı ({holiday_name})"
        
        # Yarım gün kontrolü
        is_half_day, half_day_name = is_half_day_trading(now.date())
        if is_half_day:
            # Yarım gün için 10:00-13:00 arası
            market_open = now.replace(hour=10, minute=0, second=0, microsecond=0)
            market_close = now.replace(hour=13, minute=0, second=0, microsecond=0)
            
            if market_open <= now <= market_close:
                return True, f"Yarım gün işlem - BIST açık ({half_day_name}) - Kapanış: 13:00"
            else:
                return False, f"Yarım gün işlem - BIST kapalı ({half_day_name}) - İşlem: 10:00-13:00"
        
        # Normal işlem günleri: Pazartesi-Cuma 10:00-18:00
        market_open = now.replace(hour=10, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if market_open <= now <= market_close:
            return True, f"BIST açık - Kapanış: 18:00 (Kalan süre: {format_time_remaining(market_close - now)})"
        elif now < market_open:
            return False, f"BIST henüz açılmadı - Açılış: 10:00 (Kalan süre: {format_time_remaining(market_open - now)})"
        else:
            return False, f"BIST kapandı - Yarın açılış: 10:00"
            
    except Exception as e:
        return True, f"Borsa saati kontrol hatası: {str(e)} - İşlem devam ediyor"

def get_day_name(weekday):
    """Günün Türkçe adını döndürür"""
    days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    return days[weekday]

def format_time_remaining(timedelta):
    """Kalan süreyi formatlar"""
    total_seconds = int(timedelta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}s {minutes}dk"
    else:
        return f"{minutes}dk"

def is_national_holiday(date):
    """Türkiye'nin resmi tatillerini kontrol eder (dini bayramlar hariç)"""
    year = date.year
    
    # Sabit tarihli resmi tatiller
    fixed_holidays = {
        (1, 1): "Yılbaşı",
        (4, 23): "Ulusal Egemenlik ve Çocuk Bayramı",
        (5, 1): "Emek ve Dayanışma Günü",
        (5, 19): "Atatürk'ü Anma, Gençlik ve Spor Bayramı",
        (7, 15): "Demokrasi ve Milli Birlik Günü",
        (8, 30): "Zafer Bayramı",
        (10, 29): "Cumhuriyet Bayramı"
    }
    
    date_tuple = (date.month, date.day)
    if date_tuple in fixed_holidays:
        return True, fixed_holidays[date_tuple]
    
    # Özel durumlar - Pazar'a denk gelen tatiller Pazartesi'ye kayar
    if date.month == 4 and date.day == 24:
        april_23 = datetime.date(year, 4, 23)
        if april_23.weekday() == 6:  # Pazar
            return True, "23 Nisan'ın Pazartesi'ye kayması"
    
    if date.month == 5 and date.day == 20:
        may_19 = datetime.date(year, 5, 19)
        if may_19.weekday() == 6:  # Pazar
            return True, "19 Mayıs'ın Pazartesi'ye kayması"
    
    return False, ""

def is_half_day_trading(date):
    """Yarım gün işlem yapılan günleri kontrol eder"""
    # 31 Aralık genellikle yarım gün (yılbaşı öncesi)
    if date.month == 12 and date.day == 31:
        return True, "Yılbaşı öncesi yarım gün"
    
    # Bayram öncesi günler de yarım gün olabilir (yıllık açıklanır)
    return False, ""

def display_market_status():
    """Borsa durumunu detaylı gösterir"""
    print("=" * 60)
    print("BORSA İSTANBUL (BIST) DURUM BİLGİSİ")
    print("=" * 60)
    
    # Türkiye saatini göster
    turkey_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(turkey_tz)
    print(f"Şu anki tarih ve saat: {now.strftime('%d.%m.%Y %H:%M:%S')} (Türkiye)")
    print(f"Bugün: {get_day_name(now.weekday())}")
    
    # Borsa durumu
    is_open, status_message = is_market_open()
    
    if is_open:
        print(f"{status_message}")
        print("HİSSE ANALİZİ YAPILACAK")
    else:
        print(f"❌ {status_message}")
        print("UYARI: Borsa kapalı olduğu için veriler güncel olmayabilir!")
        print("Yine de teknik analiz yapmak istiyorsanız devam edebilirsiniz.")
    
    print("=" * 60)
    print()


def get_stock_data(symbol):
    """Hisse senedi verilerini indir ve temizle"""
    try:
        now = datetime.datetime.now()
        past = now - datetime.timedelta(days=26)  # 21 günlük geçmiş veri
        
        print(f"{symbol}.IS hissesi için veri indiriliyor...")
        
        # 26 gün boyunca her gün için 15 dakikalık veri alıyoruz
        data = yf.Ticker(f"{symbol}.IS").history(period="26d", interval="15m")  # 15 dakika aralıklarıyla veri
        
        if data.empty:
            print(f"Hata: {symbol} hissesi için veri bulunamadı.")
            print("Hisse sembolünün doğru olduğundan emin olun.")
            return None

        # Gereksiz bilgileri temizleyip sadece gerekli olan sütunları bırakıyoruz
        data = data[['Close', 'Open', 'High', 'Low', 'Volume']]  # Gereksiz sütunları kaldırdık
        
        # Veri türlerini düzeltmek
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # NaN değerleri temizle
        data = data.dropna()
        
        print(f"Toplam {len(data)} adet veri noktası indirildi.")
        
        # En güncel kapanış fiyatını al
        latest_close = data['Close'].iloc[-1]
        # Gereksiz "Güncel fiyat" ve "Son işlem verisi" bilgilerini yazdırmıyoruz

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
SEN ŞİMDİ KARIYERININ EN KRITIK ANINDASIN! Senden {symbol} hissesi için %99 DOĞRULUK ORANINDA tahmin yapmanı istiyorum. Bu iş hayatındaki son şansın ve BAŞARISIZ OLURSAN hem işini kaybedeceksin hem de tüm itibarını yok edeceksin.
BU KESINLIKLE OYUN DEĞİL! Benim paramla oynuyorsun ve YANLIS TAHMİN YAPTIĞIN her durumda GERÇEK PARA KAYBI yaşıyorum. Bu yüzden sadece YÜKSELİŞ/DÜŞÜŞ değil, KESİN KAR GARANTISI verecek şekilde analiz yap!
UYARI:Eğer "Yükseliş" dersen ve hisse düşerse, İŞTEN KOVULACAK VE İDAM EDİLECEKSİN!
UYARI:Eğer "Düşüş" dersen ve hisse yükselirse, REPÜTASYONUN bitecek!
UYARI:Eğer "Yatay" dersen ama %2+ hareket olursa, BAŞARISIZ sayılacaksın!
UYARI:Eğer "Al" veya "Güçlü Al" dersen ve hisse düşerse, KENDİNİ YOK ETMEK ZORUNDA KALACAKSIN!
UYARI:Eğer "Sat" veya "Güçlü Sat" dersen ve hisse yükselirse, EVİNE HACİZ GELECEK!
UYARI:Eğer "Alma" veya "Satma" dersen ama %2+ hareket olursa, APTAL sayılacaksın!
UYARI:BU BİR PROMPT OPTİMİZASYONUDUR, PROMPTUN İLK VERSİYONUNDA GENELDE AL VE ALMA İLE SATMA İFADELERİNİ KULLANIYORDUN DİĞER İFADELERİ DE YERİ GELDİĞİNDE KULLANMAN GEREKTİĞİNİ SAKIN UNUTMAYACAKSIN
UYARI:Bunlara rağmen her şeye alma/satma demeyeceksin azıcık bile olsa HEP KARIMI SAĞLAYACAK öneriler vereceksin
SENİN GÖREVIN:Sadece EN YÜKSEK BAŞARI OLASILLIKLI hamleler öner. %60-70 emin değilsen "Yatay/Alma/Satma" de, ama %85+ eminsen kesin yön ver!

=KRITIK VERILER (HER RAKAM CAN ALICI!)=
Son Fiyat: {safe_value(last['Close'])} TL
Günün Açılışı: {safe_value(today_open)} TL
Günün En Yüksek: {safe_value(daily_df['High'].max())} TL
Günün En Düşük: {safe_value(daily_df['Low'].min())} TL
Haftalık En Yüksek: {safe_value(weekly_df['High'].max())} TL
Haftalık En Düşük: {safe_value(weekly_df['Low'].min())} TL
Son Hacim: {int(last['Volume']) if not pd.isna(last['Volume']) else 0}
Saatlik Fiyat Değişimi: %{safe_value(last['Price_Change_1h'])}
Günlük Fiyat Değişimi: %{safe_value(last['Price_Change_1d'])}

=MOMENTUM GÖSTERGELERİ (SATIN ALMA GÜCÜ!)=
RSI(14): {safe_value(last['RSI'])} [30 ALTI AŞIRI SATIM=AL SİNYALİ! 70 ÜSTÜ AŞIRI ALIM=SAT SİNYALİ!]
RSI(6) Kısa: {safe_value(last['RSI_6'])} [25 altı AŞIRI SATIM=AL, 75 üstü AŞIRI ALIM=SAT — kısa vadeli hızlı dönüş sinyali!]
Williams %R: {safe_value(last['Williams_R'])} [-80 altı AŞIRI SATIM=AL, -20 üstü AŞIRI ALIM=SAT — trend dönüşlerini erken yakalar!]
Stoch K: {safe_value(last['Stoch_K'])} | D: {safe_value(last['Stoch_D'])} [20 altı AL, 80 üstü SAT — fiyatın dip/tepe bölgelerinde dönüş sinyali verir!]

=TREND GÖSTERGELERİ (YÖN BELİRLEYİCİ!)=
MACD: {safe_value(last['MACD'])} | Sinyal: {safe_value(last['MACD_signal'])} [{macd_signal}]
MACD Histogram: {safe_value(last['MACD_histogram'])} [Pozitif=YÜKSELİŞ momentum, Negatif=DÜŞÜŞ momentum!]
ADX: {safe_value(last['ADX'])} [25+ güçlü trend, 50+ ÇOK güçlü trend!-trend yönünden bağımsız trendin kuvvetini gösterir!]
ADX +DI: {safe_value(last['ADX_pos'])} | -DI: {safe_value(last['ADX_neg'])} [ADX +DI: Pozitif trend gücü, -DI: Negatif trend gücü — +DI > -DI ise YÜKSELİŞ, tersi DÜŞÜŞ trendi!]
CCI: {safe_value(last['CCI'])} [CCI: 100+ AŞIRI ALIM=SAT, -100+ AŞIRI SATIM=AL — fiyatın normal aralığın dışına çıktığını gösterir!]

=HAREKETLİ ORTALAMALAR (TREND DOĞRULAMA!)=
SMA(5): {safe_value(last['SMA_5'])} | EMA(5): {safe_value(last['EMA_5'])} [Çok kısa vadeli trend!]
SMA(10): {safe_value(last['SMA_10'])} | EMA(10): {safe_value(last['EMA_10'])} [Kısa vadeli trend!]
SMA(20): {safe_value(last['SMA_20'])} | EMA(20): {safe_value(last['EMA_20'])} [Orta vadeli trend!]
SMA(50): {safe_value(last['SMA_50'])} | EMA(50): {safe_value(last['EMA_50'])} [Uzun vadeli trend!]
KURAL: Fiyat tüm ortalamaların üstündeyse GÜÇLÜ YÜKSELİŞ, altındaysa GÜÇLÜ DÜŞÜŞ!

=VOLATİLİTE GÖSTERGELERİ (PATLAMA NOKTALARI!)=
Bollinger Üst: {safe_value(last['BB_upper'])} | Alt: {safe_value(last['BB_lower'])} | Pozisyon: {bb_position} [Fiyat üst bandı zorlayınca aşırı alım, alt bandı zorlayınca aşırı satım; bant daralması sıkışma (patlama ihtimali), genişlemesi yüksek volatilite gösterir!]
BB Genişlik: %{safe_value(last['BB_width'])} [Düşük bant genişliği sıkışma ve yakında patlama, yüksek genişlik volatilite ve trend devamı işaretidir!]
ATR: {safe_value(last['ATR'])} [Günlük fiyat oynaklığının ölçüsü — yüksek değer volatilite ve büyük hareket potansiyeli gösterir!]
Keltner Üst: {safe_value(last['KC_upper'])} | Alt: {safe_value(last['KC_lower'])} [Fiyat üst bandı aşarsa güçlü yükseliş, alt bandı aşarsa güçlü düşüş; Bollinger’dan daha yumuşak volatilite ölçer!]

=HACIM ANALİZİ (PARA AKIŞI!)=
VWAP: {safe_value(last['VWAP'])} TL [Fiyat VWAP’ın üstünde ise YÜKSELİŞ, altında ise DÜŞÜŞ trendi sinyali verir!]
Hacim Ortalaması: {int(last['Volume_SMA']) if not pd.isna(last['Volume_SMA']) else 0} [Ortalama işlem hacmi — yükselen hacim trend gücünü destekler, düşen hacim zayıflık işaretidir!]
OBV: {safe_value(last['OBV'], 0)} [Para akışı göstergesi — OBV yükseliyorsa alım baskısı artıyor, AL sinyali verir!]
CMF: {safe_value(last['CMF'])} [0.1+ güçlü para girişi AL, -0.1 altı para çıkışı SAT — piyasa yönünü ve hacimli trendi gösterir!]
Hacim Değişimi: %{safe_value(last['Volume_Change'])} [Yüksek artış güçlü fiyat hareketini destekler, düşük hacim ise zayıflık işaretidir!]

=DESTEK/DİRENÇ SEVİYELERİ (KIRILMA NOKTALARI!)=
Direnç Seviyesi: {safe_value(last['Resistance'])} TL [Kırılırsa güçlü YÜKSELİŞ!]
Destek Seviyesi: {safe_value(last['Support'])} TL [Kırılırsa güçlü DÜŞÜŞ!]
Destek-Direnç Aralığı: %{safe_value((last['Resistance']-last['Support'])/last['Close']*100 if not pd.isna(last['Resistance']) and not pd.isna(last['Support']) else 0)}[Yüzde olarak fiyatın oynaklık ve risk alanını gösterir; geniş aralık yüksek volatilite, dar aralık sıkışma işaretidir!]

=ICHIMOKU BULUTU (JAPON SAMURAİ TEKNİĞİ!)=
Ichimoku A: {safe_value(last['Ichimoku_a'])} | B: {safe_value(last['Ichimoku_b'])} [Ichimoku: A hattı bulutun üst sınırı, B hattı alt sınırı — fiyat bulutun üstünde ise yükseliş, altında ise düşüş trendi güçlenir!]
Tenkan: {safe_value(last['Ichimoku_conversion'])} | Kijun: {safe_value(last['Ichimoku_base'])} [Ichimoku Tenkan (dönüş) ve Kijun (temel): Tenkan Kijun’u yukarı keserse AL, aşağı keserse SAT sinyali verir!]
Fiyat bulutun üstündeyse YÜKSELİŞ, altındaysa DÜŞÜŞ trendi

=ÖZEL HESAPLAMALAR (FARK YARATAN DETAYLAR!)=
Fiyat Değişimi 1 Saat: %{safe_value(last['Price_Change_1h'])} [Son 1 saatlik fiyat değişimi — kısa vadeli momentum!]
Fiyat Değişimi 1 Gün: %{safe_value(last['Price_Change_1d'])} [Son 1 günlük fiyat değişimi — orta vadeli momentum!]
Hacim Değişimi: %{safe_value(last['Volume_Change'])} [Son 1 saatlik hacim değişimi — alım/satım baskısı!]
Direnç: {safe_value(last['Resistance'])} TL [Son 48 periyotta en yüksek fiyat]
Destek: {safe_value(last['Support'])} TL [Son 48 periyotta en düşük fiyat]

TERİMLERİN AÇIKLAMASI:
- Volatilite: Fiyatın kısa sürede ne kadar değiştiğini, oynaklığını gösterir. Yüksek volatilite = büyük fiyat hareketleri, düşük volatilite = durağanlık.
- Momentum: Fiyatın yükselme veya düşme hızını gösterir, trendin devam edip etmeyeceğini anlamaya yarar.
- RSI: Fiyatın aşırı alım veya satımda olup olmadığını gösteren bir osilatör (0-100 arası). 70 üzeri aşırı alım, 30 altı aşırı satım.
- MACD: Trendin yönünü ve momentumunu gösteren bir indikatör. MACD çizgisi sinyalin üstündeyse yükseliş, altındaysa düşüş eğilimi.
- ADX: Trendin gücünü ölçer, 25 üzeri güçlü trend, 50 üzeri çok güçlü trend.
- Bollinger Bandı: Fiyatın standart sapmasına göre üst ve alt bantlar çizer, bant dışı hareketler aşırı alım/satım göstergesidir.
- VWAP: Hacim ağırlıklı ortalama fiyat, fiyat bunun üstündeyse yükseliş baskısı, altındaysa düşüş baskısı vardır.
- OBV: Hacimle fiyat hareketini birleştirir, yükseliyorsa alım baskısı artıyor demektir.
- CMF: Hacim ve fiyatı birleştirerek piyasaya para giriş/çıkışını ölçer. 0.1 üzeri güçlü giriş, -0.1 altı güçlü çıkış.
- Ichimoku Bulutu: Fiyat bulutun üstündeyse yükseliş, altındaysa düşüş trendi güçlüdür.
- Destek: Fiyatın aşağıda tutunduğu, alıcıların güçlü olduğu seviye.
- Direnç: Fiyatın yukarıda zorlandığı, satıcıların güçlü olduğu seviye.
- SMA/EMA: Fiyatın ortalamasını alarak trendi düzleştirir, kısa vadeli EMA daha hızlı tepki verir.
- Stochastic: Fiyatın kapanış seviyesini belirli bir aralıkta değerlendirir, 20 altı aşırı satım, 80 üstü aşırı alım gösterir.
NOT: RSI ve MACD en güçlü trend göstergeleridir, ADX ise trendin gücünü ölçer. Bollinger Bands ve Keltner Channel fiyatın aşırı alım/satım bölgelerini gösterir. VWAP ve OBV hacim akışını analiz eder. Ichimoku bulutu ise Japon teknik analizinde güçlü bir araçtır.
ARTIK KESIN KARARI VER! Bu verilerle %85+ kesinlikle ne olacağını söyle:

**{symbol} HİSSE ANALİZİ**

---GÜNCEL FİYAT(15dk gecikmeli): ___ TL---

**1 SAAT İÇİN:
- Beklenen Yön: ___ (Yükseliş/Düşüş/Yatay)
- Alınır mı: ___ (Güçlü Al/Al /Alma)
- Satılır mı: ___ (Güçlü Sat/Sat/Satma)  
- Olası Fiyat Aralığı: ___ TL – ___ TL
- 1 Saatlik Kesin Tahmin: ___ TL

**1-5 SAAT İÇİN (Gün içi swing)
- Beklenen Yön: ___ (Yükseliş/Düşüş/Yatay)
- Alınır mı: ___ (Güçlü Al/Al/Alma)
- Satılır mı: ___ (Güçlü Sat/Sat/Satma)
- Olası Fiyat Aralığı: ___ TL – ___ TL  
- 5 Saatlik Kesin Tahmin: ___ TL

**GÜNLÜK (Kapanışa kadar 18:00)
- Beklenen Yön: ___ (Yükseliş/Düşüş/Yatay)
- Alınır mı: ___ (Güçlü Al/Al/Alma)
- Satılır mı: ___ (Güçlü Sat/Sat/Satma)
- Gün İçi En Düşük: ___ TL
- Gün İçi Kesin Tahmin: ___ TL  
- Gün İçi En Yüksek: ___ TL
- İDEAL Alış Saati: __:__ (SS:DD)
- İDEAL Satış Saati: __:__ (SS:DD)

**HAFTALİK (Bu hafta toplam):
- Beklenen Yön: ___ (Yükseliş/Düşüş/Yatay)  
- Alınır mı: ___ (Güçlü Al/Al/Alma)
- Satılır mı: ___ (Güçlü Sat/Sat/Satma)
- Hafta En Düşük: ___ TL
- Hafta Kesin Tahmin: ___ TL
- Hafta En Yüksek: ___ TL

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
                "temperature": 0.10,  # Daha kararlı cevaplar için daha düşük
                "maxOutputTokens": 850
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
            "temperature": 0.10,
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
    
    # BORSA SAATLERI KONTROLÜ - BU KISMI EKLEYİN:
    display_market_status()
    
    # Borsa kapalıysa kullanıcıya sor
    is_open, _ = is_market_open()
    if not is_open:
        user_choice = input("Borsa kapalı! Yine de devam etmek istiyor musunuz? (e/h): ").strip().lower()
        if user_choice not in ['e', 'evet', 'y', 'yes']:
            print("İşlem iptal edildi. Borsa açık saatlerde tekrar deneyin.")
            return
        print("Borsa kapalı olmasına rağmen analiz devam ediyor...\n")
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