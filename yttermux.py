import subprocess
import random
import sys
import os
import time

PLAYLIST_URL = "play list linkiniz"  # Playlistiniz public olmalı

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
CHUNK_SIZE = 50
MAX_EMPTY_CHUNKS = 2
SLEEP_BETWEEN_CHUNKS = 1.5


def fetch_chunk(start: int, end: int) -> list[dict]:
    """Playlist'in [start, end] aralığını yt-dlp ile çeker."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
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
        vid_id = vid_id.strip()
        title = title.strip()
        if vid_id and title:
            chunk.append({"id": vid_id, "title": title})

    return chunk


def get_playlist_items() -> list[dict]:
    print("[+] Playlist parça parça okunuyor...\n")

    if not os.path.isfile(COOKIES_FILE):
        print("[!] cookies.txt bulunamadı, anonim devam ediliyor.\n")

    all_items: list[dict] = []
    seen_ids: set[str] = set()
    empty_streak = 0
    start = 1

    while True:
        end = start + CHUNK_SIZE - 1
        print(f"[~] {start}-{end} aralığı çekiliyor...", end=" ", flush=True)

        chunk = fetch_chunk(start, end)

        # Tekrar eden ID'leri filtrele
        new_items = [i for i in chunk if i["id"] not in seen_ids]
        for item in new_items:
            seen_ids.add(item["id"])

        if not new_items:
            empty_streak += 1
            print(f"boş (ardışık boş: {empty_streak}/{MAX_EMPTY_CHUNKS})")
            if empty_streak >= MAX_EMPTY_CHUNKS:
                print("[+] Playlist sonu algılandı, çekme tamamlandı.\n")
                break
        else:
            empty_streak = 0
            all_items.extend(new_items)
            print(f"{len(new_items)} şarkı alındı  →  toplam: {len(all_items)}")

        start += CHUNK_SIZE
        time.sleep(SLEEP_BETWEEN_CHUNKS)

    return all_items


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
