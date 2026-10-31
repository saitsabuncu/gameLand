# gameLand

PyQt6 tabanli, genisletilebilir masaustu mini oyun koleksiyonu. Zorluk seviyesine gore gruplanan oyunlar, ortak bir arayuz (`BaseGame`) uzerinden otomatik olarak menuye kaydedilir.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

## Calistirma

```bash
python main.py
```

## Klavye Kisayollari

Kisayollar `GameContainer` seviyesinde tanimlidir -- aktif oyun ne olursa olsun calisir, her oyunda ayrica tanimlanmasina gerek yoktur.

| Tus | Islev | Durum |
|-----|-------|-------|
| `R` | Aktif oyunu yeniden baslatir (`reset()`) | Aktif |
| `P` | Oyunu duraklatir/devam ettirir (`toggle_pause()`) | Rezerve -- varsayilan olarak no-op |

`toggle_pause()`, `BaseGame`'de **opsiyonel** bir kancadir. Number Guessing gibi tur bazli oyunlarda duraklatilacak bir sey olmadigi icin P tusu su an gorunur bir etki yaratmaz; bu kasitlidir. Ileride **Math Countdown** gibi zamanlayicili bir oyun eklendiginde, o oyun sadece kendi `toggle_pause()` metodunu override eder ve P otomatik olarak anlam kazanir -- `GameContainer` veya `BaseGame` tarafinda ekstra bir degisiklik gerekmez.

Metin girisi olan oyunlarda (orn. Number Guessing) `ShortcutAwareLineEdit` kullanilir: bu bilesen, kutu odaktayken bile R/P tuslarinin kisayol sistemine ulasmasini saglar, diger tum karakterler normal sekilde yazilabilir.

## Mimari

```
gameLand/
|-- main.py                      # Giris noktasi: oyunlari kesfeder, pencereyi acar
|-- settings.py                  # Global ayarlar (pencere boyutu, tema, vs.)
|-- core/
|   |-- base_game.py             # BaseGame (soyut sinif) + Difficulty enum
|   |-- game_registry.py         # GameRegistry + @register_game decorator + kilit mantigi
|   |-- achievements.py          # Achievement enum (kilit sistemi icin)
|   `-- progress_tracker.py      # ProgressTracker: kazanilan achievementleri diske kaydeder
|-- games/
|   |-- beginner/
|   |-- intermediate/
|   `-- advanced/
|-- ui/
|   |-- main_window.py           # Zorluk sekmeli dinamik menu
|   |-- game_container.py        # Aktif oyunu host eden frame + global kisayollar
|   |-- game_shortcuts.py        # Kisayol tuslarinin tek kaynagi (RESTART_KEY, PAUSE_KEY)
|   `-- shortcut_aware_line_edit.py
`-- utils/
    `-- game_loader.py           # games/ paketini recursive import eden discover_games()
```

**Yeni oyun eklemek icin:**

1. `games/<zorluk>/<oyun_adi>.py` dosyasini olustur.
2. `BaseGame`'den tureyen bir sinif yaz, `start()` ve `reset()` metotlarini implement et.
3. Sinifi `@register_game(display_name="...", difficulty=Difficulty.<SEVIYE>)` ile isaretle.

Baska hicbir dosyayi (menu, registry) elle degistirmen gerekmez -- `main.py` acilirken `games/` paketini otomatik tarar, decorator kendini registry'e kaydeder.

## Kilit Sistemi (Achievement Unlock)

Bazi oyunlar, baska oyunlarda belirli bir basari (`Achievement`) kazanilana kadar menude kilitli (🔒) gorunur ve tiklaninca kilit aciklamasini gosterir. Kilit durumu `data/progress.json` dosyasina kalici olarak kaydedilir (gitignore'da, oyuncuya ozel kayit verisi oldugu icin repoya commitlenmez), yani uygulamayi her actiginizda yeniden kazanmaniz gerekmez.

**Su an tek kilitli oyun: Hangman.** Number Guessing, Math Quiz Challenge veya Asal Sayi Avcisi'ndan **herhangi birinde** en az "Iyi/Harika" seviyesinde bir sonuc alindiginda acilir (hepsini degil, sadece birini basarmak yeterli). Gerekce: ilk 3 Beginner oyunu matematiksel, Hangman kelime bazli -- kelime oyununa gecmeden once biraz matematiksel yetkinlik gostermek bekleniyor.

**Yeni kilitli bir oyun eklemek icin**, `@register_game` decorator'una iki opsiyonel parametre eklenir:

```python
@register_game(
    display_name="...",
    difficulty=Difficulty.<SEVIYE>,
    required_achievements=frozenset({Achievement.X, Achievement.Y}),  # herhangi biri yeterli (OR)
    unlock_description="Kullaniciya gosterilecek aciklama metni",
)
```

Bu iki parametre verilmezse oyun her zaman acik kalir (mevcut tum oyunlarin varsayilan davranisi budur). Bir oyunun achievement kazandirmasi icin, performans esigine ulasildigi noktada `ProgressTracker.unlock_achievement(Achievement.X)` cagirmasi yeterlidir -- `games/beginner/number_guessing.py`, `math_quiz.py` ve `prime_number_hunter.py` icindeki ornekler referans alinabilir.

## Oyun Listesi

### Baslangic (Beginner)
- [x] Number Guessing -- 1-100 arasi sayi tahmini, sinirsiz deneme. Sert bir deneme limiti yok; bunun yerine ikili arama optimumuna (7 deneme) gore performans etiketi gosterilir: Mukemmel / Iyi is / Daha hizli olabilirdi.
- [x] Math Quiz Challenge -- 10 soruluk +/-/x/÷ testi, sure baskisi yok. Toplama/cikarma 1-50 araliginda, carpma/bolme 2-12 carpim tablosu araliginda (bolme her zaman tam sayi sonuclanir). Final ekraninda skora gore performans etiketi: Mukemmel / Harika is / Iyi ama daha pratik yapabilirsin / Daha cok pratik yapmalisin.
- [x] Asal Sayi Avcisi -- 1-100 arasi 10x10 grid, asal sayilari bul. Asala tiklarsan yesil, degilse kirmizi (yanlis sayaci artar), her buton tek tiklamalik. Sert basarisizlik durumu yok; tum asallar bulununca yanlis tiklama sayisina gore performans etiketi: Mukemmel / Harika is / Iyi ama daha dikkatli olabilirsin / Daha cok pratik yapmalisin.
- [x] Hangman -- klasik adam asmaca, 6 yanlis tahmin hakki (ASCII cizim asama asama ilerler). 3 kategori (Hayvanlar, Meyveler, Meslekler), ekran klavyesinden (29 harfli Turkce alfabe) harf secilir. Diger 3 Beginner oyunundan farkli olarak sert basarisizlik durumu var -- "asma" temasi gercek bir limit gerektiriyor; ama kazanildiginda yanlis tahmin sayisina gore performans etiketi gosterilir (Mukemmel / Harika is / Iyi is / Kil payi kurtuldun). **Baslangicta kilitli**: diger 3 oyundan birinde Iyi/Harika sonuc alinca acilir (bkz. Kilit Sistemi).

Ilk 3 Beginner oyunu ayni felsefeyi paylasir: sert bir basari/basarisizlik siniri yerine, kullaniciyi cezalandirmadan performansini gostermek. Hangman ise turunun geregi olarak klasik can/limit sistemini kullanir.

### Orta (Intermediate)
- [x] Nim Game -- klasik Nim (normal oyun), optimal strateji oynayan bilgisayara karsi. 3-4 yigin (her biri 1-7 tas), her oyunda rastgele. Bir tasa tiklayinca o tas ve sagindaki tum taslar alinir; son tasi alan kazanir. Nim-sum teorisine dayali bilgisayar hamlesi (`utils/nim_utils.py`) -- kaybedilen bir pozisyondan (nim-sum=0) kazanilamaz, bu matematiksel olarak kanitlanmistir.
- [ ] Monty Hall Problemi Simulasyonu
- [ ] Math Countdown

### Ileri (Advanced)
- [ ] 2048 Oyunu
- [ ] Sudoku Cozucu ve Oyunu
- [ ] Fraktal ve Kaos Oyunlari
