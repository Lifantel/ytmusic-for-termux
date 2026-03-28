import subprocess
import json
import random
import sys

PLAYLIST_URL = "Senin Playlist URL" # playlistiniz Public olmalı

def get_playlist_items(url):
    print("[+] Playlist okunuyor...\n")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--extractor-args", "youtube:player_client=android_music",
        "-J",
        url
    ]
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        print("[-] Playlist okunamadı.")
        sys.exit(1)
        
    data = json.loads(output)
    items = []
    for entry in data.get("entries", []):
        if entry.get("id") and entry.get("title"):
            items.append({
                "id": entry["id"],
                "title": entry["title"]
            })
    return items

def play_audio(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n Çalıyor: {title}\n")
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

def main():
    items = get_playlist_items(PLAYLIST_URL)
    print(f"\nToplam {len(items)} şarkı bulundu.\n")
    print("1 - Sırayla çal")
    print("2 - Random çal")
    print("3 - Manuel seç")
    print("4 - İlk şarkıyı seç, sonrasını random çal")
    mode = input("> ").strip()
    
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
            print(f"{i}. {item['title']}")
        while True:
            choice = input("\nŞarkı no (0 çıkış): ").strip()
            if choice == "0":
                break
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    play_audio(items[idx]["id"], items[idx]["title"])
                else:
                    print("Geçersiz.")
            else:
                print("Sayı gir.")
                
    elif mode == "4": 
        for i, item in enumerate(items, start=1):
            print(f"{i}. {item['title']}")
            
        choice = input("\nİlk çalınacak şarkının numarası: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                first_song = items[idx]
                play_audio(first_song["id"], first_song["title"])
                remaining_songs = items[:]
                remaining_songs.pop(idx)
                random.shuffle(remaining_songs)
                print("\n[+] İlk şarkı bitti, geri kalanlar karışık çalınıyor...\n")
                for item in remaining_songs:
                    play_audio(item["id"], item["title"])
            else:
                print("Geçersiz şarkı numarası.")
        else:
            print("Lütfen geçerli bir sayı girin.")
            
    else:
        print("Geçersiz seçim.")

if __name__ == "__main__":
    main()
