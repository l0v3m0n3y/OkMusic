from curl_cffi import requests
from typing import Optional, Dict, Any
import hashlib
import re
import json


class OKMusicSDK:
    def __init__(self, jsessionid: str):
        self.jsessionid = jsessionid
        self.base_url = "https://wmf.ok.ru"

        self.session = requests.Session(impersonate="chrome")

        self.common_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Origin": "https://ok.ru",
            "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
        }
        self.session.headers.update(self.common_headers)

        self.session.cookies.set("jsessionid", self.jsessionid, domain=".ok.ru")
        self.session.cookies.set("jsessionid", self.jsessionid, domain=".okcdn.ru")
        self.session.cookies.set("jsessionid", self.jsessionid, domain="wmf.ok.ru")

        # Массив из JS
        self._m = [4, 3, 5, 6, 1, 2, 8, 7, 2, 9, 3, 5, 7, 1, 4, 8, 8, 3, 4, 3, 1, 7, 3, 5, 9, 8, 1, 4, 3, 7, 2, 8]

    def _generate_client_hash(self, stream_url: str) -> str:
        """Генерирует clientHash по алгоритму из shared.js"""
        match = re.search(r"md5=([0-9a-fA-F]+)", stream_url)
        if not match:
            raise ValueError("md5 не найден в URL")

        md5_value = match.group(1)
        # MD5(md5 + "secret")
        hashed = hashlib.md5((md5_value + "secret").encode()).hexdigest()

        # Сумма всех hex-цифр
        a = sum(int(ch, 16) for ch in hashed)

        result = []
        length = len(hashed)
        for c in range(length):
            u = int(hashed[c], 16)
            n = u if c == length - 1 else int(hashed[c + 1], 16)
            result.append(str(abs(a - u * n * self._m[c])))

        return "".join(result)

    def _add_client_hash(self, stream_url: str) -> str:
        if "clientHash=" in stream_url:
            return stream_url
        client_hash = self._generate_client_hash(stream_url)
        return f"{stream_url}&client=web&clientHash={client_hash}"

    def get_stream_link(self, track_id: int, ctx: str = "my|1") -> str:
        url = f"{self.base_url}/play;jsessionid={self.jsessionid}"

        params = {
            "tid": track_id,
            "ctx": ctx,
            "client": "web",
            "locale": "ru",
            "imgfmt": "base",
        }

        headers = {
            **self.common_headers,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://ok.ru/music/profile/910722294189",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            response = self.session.post(
                url,
                params=params,
                data="",
                headers=headers,
                timeout=20,
            )

            print(f"[OKMusic] play → {response.status_code}")

            if response.status_code != 200:
                print(response.text[:400])
                return ""

            data = response.json()
            stream_url = data.get("play", "")

            if not stream_url:
                print("[OKMusic] Нет поля play в ответе:", data)
                return ""

            # Добавляем правильно сгенерированный clientHash
            return self._add_client_hash(stream_url)

        except Exception as e:
            print(f"[OKMusic] Ошибка get_stream_link: {e}")
            return ""

    def download_track(self, track_id: int, output_filename: str = "track.mp3") -> bool:
        stream_url = self.get_stream_link(track_id)
        if not stream_url:
            return False

        print(f"[OKMusic] Скачиваем:\n{stream_url}\n")

        headers = {
            **self.common_headers,
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Referer": "https://ok.ru/music/profile/910722294189",
            "sec-fetch-dest": "audio",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site",
            "Range": "bytes=0-",
        }

        try:
            response = self.session.get(
                stream_url,
                headers=headers,
                allow_redirects=True,
                timeout=60,
                stream=True,
            )

            print(f"[OKMusic] CDN статус: {response.status_code}")

            if response.status_code not in (200, 206):
                print("Заголовки:", dict(response.headers))
                return False

            with open(output_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

            print(f"[OKMusic] Сохранено → {output_filename}")
            return True

        except Exception as e:
            print(f"[OKMusic] Ошибка скачивания: {e}")
            return False

    def search(self, query: str) -> Dict[str, Any]:
        url = f"{self.base_url}/queryMixedSuggestions;jsessionid={self.jsessionid}"
        params = {"q": query, "client": "web", "locale": "ru"}

        headers = {
            **self.common_headers,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://ok.ru/",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[OKMusic] Ошибка поиска: {e}")
            return {}
