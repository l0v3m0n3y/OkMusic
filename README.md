# okmusic-api

Неофициальный Python SDK для работы со скрытым музыкальным API Одноклассников (WMF). 
Использует `curl_cffi` для идеального обхода TLS-фингерпринтинга (JA3/JA4) распределенной сети CDN Одноклассников.

## Установка

```bash
pip install okmusic-api
```

## Быстрый старт

```python
from okmusic_api import OKMusicSDK

# Твой jsessionid из кук браузера
sdk = OKMusicSDK(jsessionid="kdCHNeSo76je139vgu...")

# Поиск
results = sdk.search("jesus avgn")

# Скачивание трека целиком на диск (без пустых файлов в 0 байт)
sdk.download_track(123286133220562, "jesus_vssha.mp3")
```
