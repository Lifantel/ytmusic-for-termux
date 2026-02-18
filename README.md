# yttermux

Termux (veya herhangi bir linux dağıtımı) üzerinde çalışan, YouTube Music playlist’lerini terminalden dinlemenizi sağlayan basit bir Python aracıdır.  
`yt-dlp` ile playlist bilgilerini çeker ve `mpv` üzerinden sadece ses olarak çalar.

## Özellikler
- YouTube Music playlist okuma
- Sırayla çalma
- Rastgele (random) çalma
- Manuel şarkı seçimi
- Video indirmeden sadece ses oynatma

## Gereksinimler
- Python 3
- yt-dlp
- mpv
- Termux veya Linux ortamı

## Kurulum
```bash
pkg install python mpv
pip install yt-dlp
