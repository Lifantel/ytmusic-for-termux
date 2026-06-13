import subprocess
import random
import sys
import os

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLuWDZBLItlVSR8HoOueDFJieHPNK8uVW4"

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")


def get_playlist_items():
    print("[+] Playlist okunuyor...\n")

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
        "--print", "%(id)s|||%(title)s",
    ]

    if os.path.isfile(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    else:
        print("[!] cookies.txt bulunamadı, anonim devam ediliyor.\n")

    cmd.append(PLAYLIST_URL)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] yt-dlp hatası: {e}")
        return []

    items = []
    for line in output.strip().splitlines():
        if "|||" not in line:
            continue
        vid_id, title = line.split("|||", 1)
        vid_id = vid_id.strip()
        title = title.strip()
        if not vid_id or not title:
            continue
        items.append({"id": vid_id, "title": title})

    return items


def play_audio(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\nÇalıyor: {title}\n")

    cmd = [
        "mpv",
        "--no-video",
        "--cache=yes",
        "--demuxer-readahead-secs=20",
        "--ytdl-format=best/bestaudio/bestvideo+bestaudio",
        "--ytdl-raw-options=extractor-args=youtube:player_client=android",
        url
    ]

    subprocess.call(cmd)


def show_menu():
    print("\n1 - Sırayla çal")
    print("2 - Karışık çal")
    print("3 - Manuel seç")
    print("4 - İlk şarkıyı seç, sonrasını karışık çal")
    print("0 - Çıkış")


def select_song(items):
    for i, item in enumerate(items, start=1):
        print(f"{i:>4}. {item['title']}")


def main():
    items = get_playlist_items()

    if not items:
        print("[!] Hiç şarkı bulunamadı.")
        print("yt-dlp güncelleyin: pip install -U yt-dlp")
        print("cookies.txt dosyasını script'in yanına koyun")
        sys.exit(1)

    print(f"{len(items)} şarkı bulundu.")

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
