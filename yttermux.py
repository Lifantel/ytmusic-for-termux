import subprocess
import random
import sys
import os
import time
import json
from datetime import datetime

# YouTube Music linki public olmalı
_RAW_URL = "https://music.youtube.com/playlist?list=PLuWDZBLItlVSR8HoOueDFJieHPNK8uVW4"

def _normalize_playlist_url(url: str) -> str:
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    if "music.youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        playlist_id = qs.get("list", [None])[0]
        if playlist_id:
            return f"https://www.youtube.com/playlist?list={playlist_id}"
    return url

PLAYLIST_URL  = _normalize_playlist_url(_RAW_URL)
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE  = os.path.join(SCRIPT_DIR, "cookies.txt")
CACHE_FILE    = os.path.join(SCRIPT_DIR, "playlist_cache.json")

CHUNK_SIZE           = 50
MAX_EMPTY_CHUNKS     = 2
SLEEP_BETWEEN_CHUNKS = 1.5
CACHE_THRESHOLD      = 111  # Bu sayı ve altında gelirse youTube sorunlu, cache kullan


def load_cache() -> dict:
    if os.path.isfile(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print("[!] Cache bozuk, sıfırlanıyor.\n")
    return {"playlist_url": PLAYLIST_URL, "last_updated": None, "items": []}


def save_cache(items: list[dict]) -> None:
    data = {
        "playlist_url": PLAYLIST_URL,
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "total": len(items),
        "items": items,
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[+] Cache güncellendi → {CACHE_FILE}  ({len(items)} şarkı)\n")
    except OSError as e:
        print(f"[!] Cache yazılamadı: {e}\n")


def merge_with_cache(fresh: list[dict], cached: list[dict]) -> list[dict]:
    fresh_ids = {i["id"] for i in fresh}
    extra = [i for i in cached if i["id"] not in fresh_ids]
    return fresh + extra

def fetch_chunk(start: int, end: int) -> list[dict]:
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
        "--extractor-args", "youtube:player_client=web_music,web",
        "--playlist-items", f"{start}-{end}",
        "--print", "%(id)s|||%(title)s",
    ]
    if os.path.isfile(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    cmd.append(PLAYLIST_URL)

    result = subprocess.run(cmd, capture_output=True, text=True)

    chunk = []
    for line in result.stdout.strip().splitlines():
        if "|||" not in line:
            continue
        vid_id, title = line.split("|||", 1)
        vid_id, title = vid_id.strip(), title.strip()
        if vid_id and title:
            chunk.append({
                "id":    vid_id,
                "title": title,
                "url":   f"https://www.youtube.com/watch?v={vid_id}",
            })
    return chunk


def fetch_from_youtube() -> list[dict]:
    print("[+] Playlist YouTube'dan parça parça çekiliyor...\n")
    if not os.path.isfile(COOKIES_FILE):
        print("[!] cookies.txt bulunamadı, anonim devam ediliyor.\n")

    all_items: list[dict] = []
    seen_ids:  set[str]   = set()
    empty_streak = 0
    start = 1

    while True:
        end = start + CHUNK_SIZE - 1
        print(f"[~] {start}-{end} aralığı çekiliyor...", end=" ", flush=True)

        chunk = fetch_chunk(start, end)
        new_items = [i for i in chunk if i["id"] not in seen_ids]
        for item in new_items:
            seen_ids.add(item["id"])

        if not new_items:
            empty_streak += 1
            print(f"boş (ardışık boş: {empty_streak}/{MAX_EMPTY_CHUNKS})")
            if empty_streak >= MAX_EMPTY_CHUNKS:
                print("[+] Playlist sonu algılandı.\n")
                break
        else:
            empty_streak = 0
            all_items.extend(new_items)
            print(f"{len(new_items)} şarkı  →  toplam: {len(all_items)}")

        start += CHUNK_SIZE
        time.sleep(SLEEP_BETWEEN_CHUNKS)

    return all_items


def get_playlist_items() -> list[dict]:
    cache     = load_cache()
    cached    = cache.get("items", [])
    cache_ts  = cache.get("last_updated", "hiç")

    if cached:
        print(f"[i] Cache: {len(cached)} şarkı  (son güncelleme: {cache_ts})")
    fresh = fetch_from_youtube()

    if fresh:
        if len(fresh) <= CACHE_THRESHOLD:
            if cached:
                print(f"[!] YouTube {len(fresh)} şarkı verdi (≤ {CACHE_THRESHOLD} eşiği).")
                print(f"[+] Cache kullanılıyor: {len(cached)} şarkı.\n")
                return cached
            else:
                print(f"[!] YouTube {len(fresh)} şarkı verdi ve cache yok, elimizdekiyle devam.\n")
                return fresh
        if len(fresh) > len(cached):
            save_cache(fresh)
        else:
            print(f"[i] Cache zaten güncel, değişiklik yok.\n")

        return fresh
    if cached:
        print(f"[!] YouTube'dan hiç veri gelmedi, cache kullanılıyor ({len(cached)} şarkı).\n")
        return cached

    return []

def play_audio(video_id: str, title: str) -> None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\nÇalıyor: {title}\n")
    cmd = [
        "mpv",
        "--no-video",
        "--cache=yes",
        "--demuxer-readahead-secs=20",
        "--ytdl-format=best/bestaudio/bestvideo+bestaudio",
        "--ytdl-raw-options=extractor-args=youtube:player_client=android",
        url,
    ]
    subprocess.call(cmd)

def show_menu() -> None:
    print("\n1 - Sırayla çal")
    print("2 - Karışık çal")
    print("3 - Manuel seç")
    print("4 - İlk şarkıyı seç, sonrasını karışık çal")
    print("0 - Çıkış")


def select_song(items: list[dict]) -> None:
    for i, item in enumerate(items, start=1):
        print(f"{i:>4}. {item['title']}")


def main() -> None:
    items = get_playlist_items()

    if not items:
        print("[!] Hiç şarkı bulunamadı.")
        print("yt-dlp güncelleyin: pip install -U yt-dlp")
        print("cookies.txt dosyasını script'in yanına koyun")
        sys.exit(1)

    print(f"Toplam {len(items)} şarkı yüklendi.")

    while True:
        show_menu()
        mode = input("\n> ").strip()

        if mode == "0":
            break

        elif mode == "1":
            for item in items:
                play_audio(item["id"], item["title"])

        elif mode == "2":
            shuffled = items[:]
            random.shuffle(shuffled)
            for item in shuffled:
                play_audio(item["id"], item["title"])

        elif mode == "3":
            select_song(items)
            while True:
                choice = input("\nŞarkı no (0 = geri): ").strip()
                if choice == "0":
                    break
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(items):
                        play_audio(items[idx]["id"], items[idx]["title"])
                    else:
                        print(f"[!] 1 ile {len(items)} arasında girin.")
                else:
                    print("[!] Sayı girin.")

        elif mode == "4":
            select_song(items)
            choice = input("\nİlk şarkının numarası: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    play_audio(items[idx]["id"], items[idx]["title"])
                    remaining = [s for i, s in enumerate(items) if i != idx]
                    random.shuffle(remaining)
                    print("\n[+] Geri kalanlar karışık çalınıyor...\n")
                    for item in remaining:
                        play_audio(item["id"], item["title"])
                else:
                    print(f"[!] 1 ile {len(items)} arasında girin.")
            else:
                print("[!] Sayı girin.")

        else:
            print("[!] Geçersiz seçim.")


if __name__ == "__main__":
    main()
