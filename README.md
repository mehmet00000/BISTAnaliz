# 📈 BIST Hisse Tahmin Aracı

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Türk Borsası (BIST) için Gelişmiş Teknik Analiz Aracı**

Birden fazla yapay zeka modeli ve kapsamlı teknik göstergeleri kullanarak yüksek doğrulukta tahminler sunan gelişmiş Python aracı.

## 🚀 Özellikler

- **Çoklu Yapay Zeka Analizi**: Google Gemini 2.0 Flash, X.AI Grok-3 ve Groq Llama modellerini kullanır
- **Kapsamlı Teknik Göstergeler**: RSI, MACD, Bollinger Bands, Ichimoku dahil 30+ gösterge
- **Gerçek Zamanlı Veri**: Yahoo Finance üzerinden 15 dakikalık güncel veriler
- **Çoklu Zaman Dilimi**: 1 saat, 5 saat, günlük ve haftalık tahminler
- **Gelişmiş Momentum Analizi**: Özel momentum ve hacim göstergeleri
- **Destek/Direnç Seviyeleri**: Otomatik olarak hesaplanır

## 📊 Kullanılan Teknik Göstergeler

### Momentum Göstergeleri
- RSI (14 ve 6 periyot)
- Williams %R
- Stokastik Osilatör (K & D)

### Trend Göstergeleri
- MACD, Sinyal ve Histogram
- ADX, +DI ve -DI
- CCI (Commodity Channel Index)

### Hareketli Ortalamalar
- Basit Hareketli Ortalamalar (5, 10, 20, 50)
- Üssel Hareketli Ortalamalar (5, 10, 20, 50)

### Volatilite Göstergeleri
- Bollinger Bantları ve Genişliği
- ATR (Average True Range)
- Keltner Kanalları

### Hacim Göstergeleri
- VWAP (Volume Weighted Average Price)
- OBV (On-Balance Volume)
- CMF (Chaikin Money Flow)

### Japon Mum Grafiği Analizi
- Ichimoku Bulutu (Tam kurulum)

## 🛠️ Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- Gerçek zamanlı veri ve AI analizi için internet bağlantısı

### Hızlı Kurulum
```bash
# Reposu klonlayın
git clone https://github.com/mehmet00000/BISTAnaliz.git
cd BISTAnaliz

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
python borsa.py
```

### Manuel Kurulum
```bash
pip install yfinance pandas numpy requests ta
```

## 🔑 API Yapılandırması

AI analizleri için API anahtarlarına ihtiyaç vardır. Bunları ortam değişkeni olarak tanımlayabilirsiniz:

### Ortam Değişkenleri (Tavsiye Edilen)
```bash
export GEMINI_API_KEY="gemini_api_anahtarınız"
export XAI_API_KEY="xai_api_anahtarınız"
export GROQ_API_KEY="groq_api_anahtarınız"
```

### API Anahtarlarını Alma
1. **Google Gemini**: [Google AI Studio](https://aistudio.google.com/)
2. **X.AI Grok**: [X.AI Console](https://console.x.ai/)
3. **Groq**: [Groq Console](https://console.groq.com/)

## 💡 Kullanım

### Temel Kullanım
```bash
python borsa.py
```

İstendiğinde bir BIST hisse sembolü girin (örnek: THYAO, AKBNK, GARAN, ISCTR)

### Örnek Çıktı
```
**THYAO HİSSE ANALİZİ**

---GÜNCEL FİYAT(15dk gecikmeli): 279.75 TL---

**1 SAAT İÇİN:
- Beklenen Yön: Yatay
- Alınır mı: Alma
- Satılır mı: Satma
- Olası Fiyat Aralığı: 278.50 TL – 281.00 TL
- 1 Saatlik Kesin Tahmin: 279.50 TL

**1-5 SAAT İÇİN (Gün içi swing)
- Beklenen Yön: Yükseliş
- Alınır mı: Al
- Satılır mı: Satma
- Olası Fiyat Aralığı: 279.00 TL – 283.00 TL
- 5 Saatlik Kesin Tahmin: 282.00 TL

**GÜNLÜK (Kapanışa kadar 18:00)
- Beklenen Yön: Yükseliş
- Alınır mı: Al
- Satılır mı: Satma
- Gün İçi En Düşük: 278.00 TL
- Gün İçi Kesin Tahmin: 284.00 TL
- Gün İçi En Yüksek: 286.00 TL
- İDEAL Alış Saati: 11:00
- İDEAL Satış Saati: 16:00

**HAFTALİK (Bu hafta toplam):
- Beklenen Yön: Yükseliş
- Alınır mı: Al
- Satılır mı: Satma
- Hafta En Düşük: 277.00 TL
- Hafta Kesin Tahmin: 290.00 TL
- Hafta En Yüksek: 295.00 TL

 DİKKAT: Bu tahminler %98 doğruluk hedefiyle yapılmıştır.
SORUMLU YATIRIM: Kendi riskinizi değerlendirin!

```

## 📋 Desteklenen Hisseler

Tüm BIST (Borsa İstanbul) hisseleriyle çalışır. Popüler örnekler:

- **Bankacılık**: AKBNK, GARAN, ISCTR, YKBNK, HALKB 
- **Enerji**: TUPRS, PETKM, AYGAZ 
- **Havacılık**: THYAO, PGSUS 
- **Teknoloji**: ASELS, LOGO, INDES 
- **Perakende**: MGROS, SOKM, CIMSA 

## 🏗️ Mimari

```
borsa.py
├── Veri Toplama (yfinance)
├── Teknik Analiz (ta kütüphanesi)
├── AI Analiz Zinciri
│   ├── Google Gemini 2.0 Flash (Birincil)
│   ├── X.AI Grok-3 (Yedek)
│   └── Groq Llama (Alternatif)
└── Tahmin Çıktısı
```

## ⚙️ Yapılandırma

### Veri Parametreleri
- **Zaman Aralığı**: 15 dakika 
- **Geriye Dönük Süre**: 21 gün 
- **Minimum Veri Noktası**: 100 

### AI Model Öncelikleri
1. **Gemini 2.0 Flash** (Birincil - En yüksek doğruluk)
2. **Grok-3** (Yedek - Finans uzmanlığı)
3. **Groq Llama** (Alternatif - Hızlı işlem)

## 🧪 Teknik Detaylar

### Veri İşleme
- Otomatik veri temizleme ve doğrulama 
- Çoklu indeks sütun yönetimi 
- NaN değer yönetimi 
- Hacim ve fiyat momentumu hesaplamaları 

### Gösterge Hesaplamaları
- Gerçek zamanlı 30+ teknik gösterge 
- Yetersiz veri için hata yönetimi 
- Özel destek/direnç seviyesi tespiti 
- Gelişmiş volatilite ölçümleri 

## 📈 Doğruluk ve Performans

- **Hedef Doğruluk**: Kısa vadeli tahminlerde %85+ 
- **Veri Gecikmesi**: ~15 dakika (Yahoo Finance limiti) 
- **İşleme Süresi**: Analiz başına 5-15 saniye 
- **Başarı Oranı**: Piyasa koşullarına ve zaman dilimine göre değişir 

## ⚠️ Yasal Uyarı

**ÖNEMLİ RİSK UYARISI**

Bu araç yalnızca eğitim ve bilgilendirme amacıyla tasarlanmıştır. Finansal tavsiye, yatırım önerisi veya al-sat sinyali niteliği taşımaz.

- **Geçmiş performans geleceği garanti etmez** 
- **Tüm yatırımlar kayıp riski taşır** 
- **Piyasa tahminleri doğası gereği belirsizdir** 
- **Kendi araştırmanızı mutlaka yapın** 
- **Kaybetmeyi göze alamayacağınız parayla yatırım yapmayın** 
- **Profesyonel finans danışmanına başvurmanız önerilir**

Bu aracı kullanarak yaşanacak mali kayıplardan sorumluluk kabul etmiyorum.

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır – detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- Gerçek zamanlı piyasa verisi için **Yahoo Finance** 
- Teknik analiz göstergeleri için **TA-Lib Python** 
- AI analiz yetenekleri için **Google, X.AI, Groq** 
- Türk borsa verisi için **BIST**

## 📞 Destek

- **Hatalar**: [GitHub Issues](https://github.com/mehmet00000/BISTAnaliz/issues) 
- **Tartışmalar**: [GitHub Discussions](https://github.com/mehmet00000/BISTAnaliz/discussions) 
- **E-posta**: [m3081@proton.me](mailto:m3081@proton.me) 

## 🔄 Değişiklik Günlüğü

### v2.0.0 (Güncel)
- AI optimizasyonu
- Gösterge optimizasyonları
- Kod optimizasyonları

### v1.1.0
- Borsa Kapalı uyarısı eklendi

### v1.0.0
- İlk sürüm
- Çoklu AI entegrasyonu
- 30+ teknik gösterge
- BIST desteği
- Gerçek zamanlı analiz

---

**⭐ Bu aracı faydalı bulduysanız GitHub’da yıldız vermeyi unutmayın!**

*Türk yatırımcı topluluğu için sevgiyle geliştirildi*
