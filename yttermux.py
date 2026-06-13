import subprocess
import random
import sys

PLAYLIST_URL = "Senin Playlist URL"  # Playlist'iniz Public olmalı


def get_playlist_items(url):
    print("[+] Playlist okunuyor...\n")

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
        "--print", "%(id)s|||%(title)s",
        url
    ]

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Hata oluştu: {e}")
        return []

    items = []
    for line in output.strip().splitlines():
        line = line.strip()
        if "|||" not in line:
            continue
        vid_id, title = line.split("|||", 1)
        vid_id = vid_id.strip()
        title = title.strip()
        if not vid_id or not title or vid_id.lower() in ("na", "none", "[deleted]"):
            continue
        items.append({"id": vid_id, "title": title})

    return items


def play_audio(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n🎵 Çalıyor: {title}\n")
    cmd = [
        "mpv",
        "--no-video",
        "--cache=yes",
        "--demuxer-readahead-secs=20",
        "--ytdl-format=bestaudio/best",
        "--ytdl-raw-options=extractor-args=youtube:player_client=android",
        url
    ]
    subprocess.call(cmd)


def main():
    items = get_playlist_items(PLAYLIST_URL)

    if not items:
        print("[!] Hiç şarkı bulunamadı. Playlist URL'sini ve erişim iznini kontrol edin.")
        sys.exit(1)

    print(f"Toplam {len(items)} şarkı bulundu.\n")
    print("1 - Sırayla çal")
    print("2 - Karışık çal")
    print("3 - Manuel seç")
    print("4 - İlk şarkıyı seç, sonrasını karışık çal")

    mode = input("\n> ").strip()

    if mode == "1":
        for item in items:
            play_audio(item["id"], item["title"])

    elif mode == "2":
        shuffled = items[:]
        random.shuffle(shuffled)
        for item in shuffled:
            play_audio(item["id"], item["title"])

    elif mode == "3":
        for i, item in enumerate(items, start=1):
            print(f"{i:>4}. {item['title']}")
        while True:
            choice = input("\nŞarkı no (0 = çıkış): ").strip()
            if choice == "0":
                break
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    play_audio(items[idx]["id"], items[idx]["title"])
                else:
                    print(f"[!] Geçersiz numara. 1 ile {len(items)} arasında girin.")
            else:
                print("[!] Lütfen bir sayı girin.")

    elif mode == "4":
        for i, item in enumerate(items, start=1):
            print(f"{i:>4}. {item['title']}")
        choice = input("\nİlk çalınacak şarkının numarası: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                first_song = items[idx]
                play_audio(first_song["id"], first_song["title"])
                remaining = [s for i, s in enumerate(items) if i != idx]
                random.shuffle(remaining)
                print("\n[+] İlk şarkı bitti, geri kalanlar karışık çalınıyor...\n")
                for item in remaining:
                    play_audio(item["id"], item["title"])
            else:
                print(f"[!] Geçersiz numara. 1 ile {len(items)} arasında girin.")
        else:
            print("[!] Lütfen geçerli bir sayı girin.")

    else:
        print("[!] Geçersiz seçim.")


if __name__ == "__main__":
    main()

