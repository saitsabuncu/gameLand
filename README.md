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
| `P` | Oyunu duraklatir/devam ettirir (`toggle_pause()`) | Aktif (**Math Countdown**, **Kaos Oyunu**'nda) |

`toggle_pause()`, `BaseGame`'de **opsiyonel** bir kancadir. Tur bazli oyunlarda (Number Guessing, Nim Game, Monty Hall, 2048, Sudoku, vs.) duraklatilacak bir sey olmadigi icin P tusu bu oyunlarda gorunur bir etki yaratmaz; bu kasitlidir. **Math Countdown**, projenin ilk zamanlayicili oyunu olarak `toggle_pause()`'u override eder: P'ye basinca `QTimer` durur/devam eder, giris kutusu ve gonder butonu da duraklama sirasinda devre disi kalir. **Kaos Oyunu** da ayni sekilde override eder -- ustelik ekrandaki ▶️/⏸ butonu da P tusuyla birebir ayni `toggle_pause()` metodunu cagirir, iki ayri duraklama kod yolu yok. Her iki durumda da `GameContainer` veya `BaseGame` tarafinda ekstra bir degisiklik gerekmedi.

Metin girisi olan oyunlarda (orn. Number Guessing) `ShortcutAwareLineEdit` kullanilir: bu bilesen, kutu odaktayken bile R/P tuslarinin kisayol sistemine ulasmasini saglar, diger tum karakterler normal sekilde yazilabilir.

## Yardim Sistemi (Nasil Oynanir?)

`GameContainer`'da her oyunda goruntulenen bir **"❓ Nasil Oynanir?"** butonu vardir. Tiklaninca aktif oyunun kurallarini aciklayan bir mesaj penceresi acilir. Tum mevcut oyunlarda (Number Guessing, Math Quiz Challenge, Asal Sayi Avcisi, Hangman, Nim Game, Monty Hall Problemi Simulasyonu, Math Countdown, 2048, Sudoku, Kaos Oyunu) bu aciklama metni tanimlidir.

**Yeni bir oyun yazarken** aciklama eklemek icin, `@register_game` decorator'una bir `instructions` parametresi gecirilir:

```python
@register_game(
    display_name="...",
    difficulty=Difficulty.<SEVIYE>,
    instructions="Oyunun kurallarini aciklayan metin.",
)
```

Bu parametre atlanirsa, yardim butonu otomatik olarak genel bir fallback mesaji gosterir ("Bu oyun icin ek aciklama eklenmedi.") -- yani yeni bir oyun icin `instructions` unutulursa uygulama hata vermez, sadece eksik bir aciklama gorunur. Baska hicbir dosyada (GameContainer, BaseGame) degisiklik gerekmez.

## Ana Menu

Zorluk sekmeleri (`Difficulty` enum'unun `.value`'lari) Turkce: **Baslangic / Orta / Ileri** -- projenin geri kalaniyla (yardim metinleri, README) dil tutarliligi icin. Her oyun karti bir ikon (`ui/main_window.py` icindeki `_GAME_ICONS` sozlugu, oyun adina gore; eslesme yoksa varsayilan 🎮), zorluk seviyesine gore renkli bir sol kenarlik (yesil=Baslangic, turuncu=Orta, mor=Ileri) ve kilitliyse gri stil + 🔒 etiketi gosterir. Yeni bir oyunun ikonu `_GAME_ICONS`'a eklenmezse uygulama hata vermez, sadece varsayilan ikonla gorunur.

Zorluk sayfalarindaki kart grid'i (`QGridLayout`), Sudoku'nun tahtasinda cozulen ayni soruna dusmemesi icin bir `QVBoxLayout` icine sarilip sonuna `addStretch(1)` eklenerek olusturulur: boylece az sayida oyun olan bir sekmede (orn. sadece 4 oyunlu Baslangic) satirlar pencerenin tamamina yayilip aralarinda devasa bosluklar birakmak yerine, ust tarafta sikisik kalir ve kalan tum bosluk kartlarin altinda toplanir.

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
|   |-- __init__.py              # from games import beginner, intermediate, advanced
|   |-- beginner/                # __init__.py o seviyedeki her oyun modulunu import eder
|   |-- intermediate/
|   `-- advanced/
|-- ui/
|   |-- main_window.py           # Zorluk sekmeli dinamik menu
|   |-- game_container.py        # Aktif oyunu host eden frame + global kisayollar
|   |-- game_shortcuts.py        # Kisayol tuslarinin tek kaynagi (RESTART_KEY, PAUSE_KEY)
|   `-- shortcut_aware_line_edit.py
|-- utils/                       # Her oyunun saf mantigi (PyQt bagimsiz, pytest ile test edilir)
`-- tests/                       # pytest suite -- bkz. Test & Paketleme
```

**Yeni oyun eklemek icin:**

1. `games/<zorluk>/<oyun_adi>.py` dosyasini olustur.
2. `BaseGame`'den tureyen bir sinif yaz, `start()` ve `reset()` metotlarini implement et.
3. Sinifi `@register_game(display_name="...", difficulty=Difficulty.<SEVIYE>)` ile isaretle.
4. Yeni modulu `games/<zorluk>/__init__.py`'deki import listesine ekle.

4. adim **zorunlu** -- ve kasitli olarak otomatik degil. Onceki surumde `games/` paketi `pkgutil.walk_packages` ile dosya sisteminde taraniyordu ("4. adim gerekmez" deniyordu), ama bu PyInstaller ile paketlenince tamamen bozuluyordu: donmus (frozen) bir derlemede saf Python modulleri diskte gevsek dosyalar olarak degil, sikistirilmis bir arsivin icinde yasar, yani `games.__path__` pkgutil'in goremedigi bir dizine isaret ediyor -- paketlenmis uygulama hicbir hata vermeden **sifir oyunla** aciliyordu (build edilip calistirilarak dogrulandi). Cozum: dosya sistemi taramasi tamamen kaldirildi, yerine `games/<seviye>/__init__.py`'de duz, statik `import` ifadeleri kullanildi -- PyInstaller statik import'lari kendiliginden takip ettigi icin artik ekstra bir `hiddenimports` bildirimine de gerek yok. Bedeli: yeni oyun eklerken bir satir import eklemek: kucuk, aciyla not gorulebilir, karsiliginda paketlendiginde de calisan bir davranis.

## Test & Paketleme

```bash
pip install -r requirements-dev.txt   # pytest + pyinstaller
```

**Testler** (`tests/`): her oyunun saf mantigi (`utils/*.py`) ve `GameRegistry`/`ProgressTracker` icin pytest testleri var -- PyQt widget'lari degil, sadece PyQt'den bagimsiz mantik test ediliyor (bu ayrim projenin basindan beri bilincli: UI testi kirilgandir, mantik testi degildir).

```bash
pytest                 # tum suite
QT_QPA_PLATFORM=offscreen pytest   # Linux'ta ekransiz (CI'da kullanilan ayar)
```

`pytest.ini`'deki `pythonpath = .` sayesinde proje kokunden veya baska bir dizinden calistirmak fark etmez. `.github/workflows/tests.yml`, her `push`/`pull request`'te Ubuntu'da testleri otomatik calistirir.

**Paketleme** (`gameland.spec`): tek-dosya bir Windows `.exe` uretir.

```bash
pyinstaller gameland.spec    # -> dist/gameLand.exe
```

`.github/workflows/release.yml`, `v*` formatinda bir tag push'landiginda (orn. `git tag v0.2.0 && git push origin v0.2.0`) once testleri calistirir, sonra Windows'ta `.exe`'yi derler ve GitHub Releases'e ekler.

**Paketlemede bulunup duzeltilen iki mimari hata** (asil neden: PyInstaller'in donmus/frozen derlemesi, "kaynak" dizini diye bir sey yoktur -- her sey gecici bir acma dizininde veya sikistirilmis bir arsivin icindedir):

1. *Oyun kesfi.* `games/` paketi eskiden `pkgutil.walk_packages` ile dosya sisteminde taraniyordu. PyInstaller'da saf Python modulleri diskte gevsek dosya olarak degil, sikistirilmis arsivin icinde durur -- `games.__path__` pkgutil'in goremedigi bir yola isaret ediyor ve **hicbir hata vermeden** sifir oyun kayitli kaliyordu (gercek bir build ile dogrulandi). Duzeltme: `games/<seviye>/__init__.py`'de duz statik `import` ifadeleri (bkz. Mimari).
2. *Achievement kaliciligi.* `progress.json`'un konumu (`settings.BASE_DIR`) proje klasorunden hesaplaniyordu; PyInstaller'da bu, calistirma bitince silinen gecici bir dizine denk geliyor -- kilitler her acilista sessizce sifirlaniyordu. Duzeltme: `settings.USER_DATA_DIR`, isletim sistemine gore gercek bir kullanici-veri dizinine isaret ediyor (bkz. Kilit Sistemi).

Her ikisi de **sessiz** basarisizliklardi -- hata vermiyor, sadece yanlis calisiyordu; bu yuzden "calisiyor gibi gorunuyor" ile "paketlenince calisiyor" arasindaki farki gorebilmek icin gercek bir `pyinstaller` build'i alip calistirarak dogrulandilar, sadece kod okuyarak degil.

## Kilit Sistemi (Achievement Unlock)

Bazi oyunlar, baska oyunlarda belirli bir basari (`Achievement`) kazanilana kadar menude kilitli (🔒) gorunur ve tiklaninca kilit aciklamasini gosterir. Kilit durumu, isletim sistemine gore degisen bir **kullanici-veri dizinindeki** `progress.json` dosyasina kalici olarak kaydedilir (`settings.USER_DATA_DIR`: Windows'ta `%APPDATA%\gameLand`, macOS'ta `~/Library/Application Support/gameLand`, Linux'ta `~/.local/share/gameLand`), yani uygulamayi her actiginizda yeniden kazanmaniz gerekmez. Bu konum, proje klasorunun **disinda** -- bilerek: daha once `BASE_DIR / "data"` (proje klasorunun icinde) kullaniliyordu, ama PyInstaller ile paketlenince `BASE_DIR` gecici bir acma dizinine (`sys._MEIPASS`) isaret ediyor ve bu dizin uygulama her kapandiginda silinip gidiyor -- yani achievementler sessizce hic kalici olmuyordu (bkz. Test & Paketleme). `python main.py` ile dogrudan calistirmada da, paketlenmis `.exe`'de de ayni kod yolu kullanilir.

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

## Oyun-Ici Seviye (GameLevel)

Bazi oyunlarda, oyuncunun oyunun **icinde** degistirebilecegi bir Kolay/Orta/Zor secenegi var -- pilot uygulama **Sudoku**'da (ipucu hucre sayisini degistiriyor). Bu, menu sekmelerini belirleyen `Difficulty` (Baslangic/Orta/Ileri) ile **kasitli olarak ayri bir enum**: `Difficulty` bir oyunun hangi sekmede yasadigini belirler (sabit, `@register_game`'de bir kez verilir), `GameLevel` ise o oyunun icindeki bir ayardir (oyuncu istedigi an degistirir, hangi sekmede oldugunu etkilemez). İkisini tek enum yapmak, oyun-ici zorlugu degistirmenin oyunu baska bir men sekmesine tasimasi gibi anlamsiz bir sonuc doguracakti.

**Her oyunda zorunlu degil** -- `toggle_pause()` gibi opsiyonel: anlamli bir zorluk ekseni olmayan oyunlarda (Monty Hall, Kaos Oyunu, ...) hic kullanilmaz. Yeni bir oyuna eklemek icin (Sudoku'daki (`games/advanced/sudoku.py`) ornegi referans alinabilir):

1. Oyunun kendi dosyasinda, seviyeden etkilenen parametre(ler) icin bir `dict[GameLevel, ...]` esleme tanimla (orn. Sudoku'da ipucu sayisi).
2. `__init__`'te `ProgressTracker.get_level("<stabil_anahtar>", default=GameLevel.MEDIUM)` ile son secimi yukle, bir `QComboBox` ile seviyeyi goster.
3. Secim degisince `ProgressTracker.set_level(...)` ile kaydet ve oyunu o seviyeyle yeniden baslat.

`<stabil_anahtar>`, `display_name` degil, sabit bir metin olmali (Sudoku'da `"sudoku"`) -- ileride goruntu adi degisirse kayitli seviyenin sifirlanmamasi icin.

## Oyun Listesi

### Baslangic (Beginner)
- [x] Number Guessing -- sayi tahmini, sinirsiz deneme. **Kolay/Orta/Zor** seviye secici (GameLevel), tahmin araligini genisletiyor: Kolay 1-50, Orta 1-100 (eski sabit davranis), Zor 1-200 -- optimal deneme sayisi (ikili arama: log2) araliga gore otomatik hesaplanir, yani Zor'da optimal/iyi esikleri de buna gore biraz genisler, ekstra bir ayar gerekmez. Sert bir deneme limiti yok; performans etiketi gosterilir: Mukemmel / Iyi is / Daha hizli olabilirdi.
- [x] Math Quiz Challenge -- 10 soruluk +/-/x/÷ testi, sure baskisi yok. Toplama/cikarma 1-50 araliginda, carpma/bolme 2-12 carpim tablosu araliginda (bolme her zaman tam sayi sonuclanir). Final ekraninda skora gore performans etiketi: Mukemmel / Harika is / Iyi ama daha pratik yapabilirsin / Daha cok pratik yapmalisin.
- [x] Asal Sayi Avcisi -- 1-100 arasi 10x10 grid, asal sayilari bul. Asala tiklarsan yesil, degilse kirmizi (yanlis sayaci artar), her buton tek tiklamalik. Sert basarisizlik durumu yok; tum asallar bulununca yanlis tiklama sayisina gore performans etiketi: Mukemmel / Harika is / Iyi ama daha dikkatli olabilirsin / Daha cok pratik yapmalisin.
- [x] Hangman -- klasik adam asmaca, 6 yanlis tahmin hakki (ASCII cizim asama asama ilerler). 3 kategori (Hayvanlar, Meyveler, Meslekler), ekran klavyesinden (29 harfli Turkce alfabe) harf secilir. Diger 3 Beginner oyunundan farkli olarak sert basarisizlik durumu var -- "asma" temasi gercek bir limit gerektiriyor; ama kazanildiginda yanlis tahmin sayisina gore performans etiketi gosterilir (Mukemmel / Harika is / Iyi is / Kil payi kurtuldun). **Baslangicta kilitli**: diger 3 oyundan birinde Iyi/Harika sonuc alinca acilir (bkz. Kilit Sistemi).

Ilk 3 Beginner oyunu ayni felsefeyi paylasir: sert bir basari/basarisizlik siniri yerine, kullaniciyi cezalandirmadan performansini gostermek. Hangman ise turunun geregi olarak klasik can/limit sistemini kullanir.

### Orta (Intermediate)
- [x] Nim Game -- klasik Nim (normal oyun), optimal strateji oynayan bilgisayara karsi. 3-4 yigin (her biri 1-7 tas), her oyunda rastgele. Bir tasa tiklayinca o tas ve sagindaki tum taslar alinir; son tasi alan kazanir. Nim-sum teorisine dayali bilgisayar hamlesi (`utils/nim_utils.py`) -- kaybedilen bir pozisyondan (nim-sum=0) kazanilamaz, bu matematiksel olarak kanitlanmistir.
- [x] Monty Hall Problemi Simulasyonu -- 3 kapi, klasik host kurali (Monty asla arabayi acmaz, asla oyuncunun kapisini acmaz). Manuel modda kapi sec, Monty bir keciyi acar, degistir/kal karari ver. Ayrica "Simule Et" ile N turu aninda kosturan toplu simulasyon var; manuel ve toplu turlar ayni degistir/kal istatistik paneline eklenir (kazanma oranlari gercek zamanli gorulur, ~%66.7 vs ~%33.3'e yakinsamasi beklenir). Saf olasilik mantigi `utils/monty_hall_utils.py`'de, UI'dan bagimsiz.
- [x] Math Countdown -- klasik Countdown sayi oyunu. Her turda 6 sayi (0-4 buyuk kart: 25/50/75/100, kalani kucuk kart: 1-10'dan iki set) ve 3 haneli hedef verilir; +-*/ ve parantezlerle 30 saniyede hedefe en yakin sonucu bulmaya calisilir. Kural: her ara sonuc pozitif tam sayi olmali, bolme kalansiz olmali -- ifade `ast` ile guvenli sekilde ayristirilip dogrulanir (`utils/countdown_utils.py`). Puanlama: tam isabet 10, +-5 ici 7, +-10 ici 5, uzaksa 0 puan; 5 tur sonunda toplam puana gore performans etiketi. **Projenin ilk gercek zamanlayicili oyunu**: `toggle_pause()` burada artik no-op degil, P tusu QTimer'i gercekten durdurup devam ettiriyor (bkz. Klavye Kisayollari).

### Ileri (Advanced)
- [x] 2048 Oyunu -- klasik sabit 4x4 grid, ok tuslariyla (Yukari/Asagi/Sol/Sag) kontrol. Ayni degerdeki komsu taslar kaydirma yonunde birlesip toplanir (klasik "tek pasta bir kez birlesme" kurali), her hamleden sonra bos bir huczeye %90 '2' / %10 '4' eklenir. 2048'e ulasinca tebrik banner'i gorunur ama oyun bitmez -- grid tamamen dolup hicbir yonde gecerli hamle kalmayana kadar devam edilebilir. Yon-bagimsiz tek bir slide-and-merge mantigi (`utils/grid2048_utils.py`) grid'i transpoze/ters cevirerek 4 yonu de ayni koddan turetir. Animasyonsuz, anlik yeniden cizim -- projenin diger oyunlariyla tutarli.
- [x] Sudoku -- klasik 9x9, **Kolay/Orta/Zor** seviye secici (ekranin ustunde, GameLevel). Seviye, baslangicta birakilan ipucu hucre sayisini belirler: Kolay 46, Orta 40, Zor 32 (uretici tek dugmesi bu -- cozum teknigine gore degil, sadece ipucu sayisina gore zorluk; uretim suresi 32'de bile ~130ms, fark edilmez). Secilen seviye `ProgressTracker` ile diske kaydedilir ve bir sonraki acilista otomatik secili gelir. Bulmaca her start()/reset()'te (ve seviye degisiminde) yeniden uretilir: once backtracking ile rastgele tam cozum uretilir, sonra "delik acma" yontemiyle hucreler rastgele sirayla bosaltilir -- her bosaltmadan sonra bulmacanin hala tek cozumu oldugu dogrulanir (degilse o hucre geri konur), yani her bulmaca garantili biricik cozumlu. Bos bir huczeye tiklayip klavyeden 1-9 yazilir; bir deger ayni satir/sutun/3x3 kutuda zaten varsa o hucre VE cakistigi hucre aninda kirmiziya doner. 3 sinirli ipucu hakki var (secili bos hucreye dogru degeri yazar). Tum hucreler cakismasiz dolunca bulmaca kilitlenir ve tamamlandi mesaji gorunur. Uretici/cozucu/cakisma mantigi `utils/sudoku_utils.py`'de UI'dan bagimsiz.
- [x] Kaos Oyunu -- klasik "Chaos Game": nokta her adimda rastgele secilen bir kosegene dogru yolun tam yarisina tasinir, binlerce tekrardan sonra duzenli bir fraktal ortaya cikar. 3 kose (ucgen) kisitlamasiz calisir ve tam olarak Sierpinski Ucgeni'ni uretir (merkez bosluk hic doldurulmaz -- headless testle dogrulandi); 4/5/6 kosede ardi ardina ayni iki secimin tekrari engellenerek anlamli bir desen zorlanir. Her nokta yoneldigi kosenin rengiyle cizilir, QTimer ile ~60fps canli olusum (hiz kaydiricisi ile ayarlanabilir), QPainter.drawPoints() ile renk bazinda toplu cizim (binlerce nokta performansli). Projenin ikinci gercek zamanlayicili oyunu: P tusu VE ekrandaki ▶️/⏸ butonu ayni `toggle_pause()` metodunu cagirir, tek bir duraklat/devam kod yolu var. Saf geometri/kisitlama mantigi `utils/chaos_game_utils.py`'de UI'dan bagimsiz. gameLand'in planlanan son oyunu -- 3 seviyedeki tum oyunlar tamamlandi.
