# 🛠 ساخت فایل exe «نوا» روی ویندوز

راهنمای کامل از صفر: نصب پایتون → تست → ساخت `Nava.exe`.
زمان لازم: حدود **۵ دقیقه** (به‌علاوه‌ی دانلود ~۱۲۰ مگابایت پکیج).

🇬🇧 English version: **[HOWTO-build-exe.md](HOWTO-build-exe.md)**

---

## ۰) پیش‌نیازها (یک‌بار برای همیشه)

| مورد | توضیح |
|---|---|
| ویندوز | ۱۰ یا ۱۱ — ۶۴ بیتی |
| پایتون | نسخه **۳.۱۰ یا بالاتر (۶۴ بیتی)** — [python.org/downloads](https://www.python.org/downloads/) |
| اینترنت | فقط برای نصب پکیج‌ها؛ خود برنامه کامل آفلاین است |

### نصب پایتون (مهم‌ترین نکته!)

1. از [python.org/downloads](https://www.python.org/downloads/) فایل **Windows installer (64-bit)** را دانلود کن.
2. در صفحه‌ی اول نصب‌کننده **تیک «Add python.exe to PATH»** را حتماً بزن ✅ — بدون این تیک دستورها کار نمی‌کنند.
3. روی **Install Now** بزن و صبر کن تمام شود.
4. برای اطمینان: `Win + R` → بنویس `cmd` → Enter، سپس:

```bat
python --version
```

اگر `Python 3.11.x` چاپ شد آماده‌ای. اگر «شناخته نشد»: `py -3 --version` را امتحان کن و از این به بعد `py -3` بنویس.

---

## ۱) راه ساده: با یک دابل‌کلیک 🖱

1. پروژه را در مسیر ساده‌ای اکسترکت کن، مثل:

```
C:\nava-player\
```

> ⚠️ مسیر را فارسی یا با کاراکترهای خاص انتخاب نکن (مثل `C:\کارهای من\نوا`)؛ بعضی ابزارهای ساخت با حروف غیرانگلیسی مشکل پیدا می‌کنند.

2. روی فایل **`build.bat`** دابل‌کلیک کن.
3. یک پنجره‌ی سیاه باز می‌شود که ۳ مرحله را انجام می‌دهد:

```
[1/3] Checking Python...           ← نصب PySide6, mutagen, pyinstaller
[2/3] Preparing the icon...        ← ساخت nava.ico
[3/3] Building dist\Nava.exe ...   ← ساخت خروجی (۱ تا ۳ دقیقه)
```

4. وقتی **`Done!`** چاپ شد، فایل نهایی اینجاست:

```
C:\nava-player\dist\Nava.exe
```

تمام! 🎉 این یک فایل تنهاست؛ می‌توانی هر جا کپی‌اش کنی.

---

## ۲) راه دستی: ۴ دستور در Command Prompt

پوشه‌ی پروژه را در File Explorer باز کن، در نوار آدرس `cmd` بنویس و Enter بزن، بعد:

```bat
REM ۱ - پکیج‌های لازم (فقط بار اول؛ حدود ۱۰۰ مگابایت)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

REM ۲ - آیکون برنامه (فقط اگر آیکون را عوض کرده‌ای)
python tools\make_ico.py

REM ۳ - ساخت
python -m PyInstaller --noconfirm --clean Nava.spec

REM ۴ - خروجی
dir dist
```

خروجی: **`dist\Nava.exe`** (حدود ۵۰ مگابایت — طبیعی است؛ موتور Qt و کدک‌های صوتی داخلش هستند).

---

## ۳) قبل از ساخت، تست کن (پیشنهادی)

```bat
python main.py
```

اگر پنجره‌ی نوا باز شد و آهنگ پخش شد، exe هم قطعاً کار می‌کند.

---

## ۴) اجرای exe و نکته‌ی SmartScreen

- روی `Nava.exe` دابل‌کلیک کن. بار اول چند ثانیه دیرتر باز می‌شود؛ از بار دوم سریع است.
- چون فایل **امضای دیجیتال** ندارد، ویندوز ممکن است پیام آبی
  «Windows protected your PC» نشان دهد → **More info → Run anyway**.
- برای حذف این هشدار در سیستم خودت (اختیاری، PowerShell):

```powershell
Unblock-File .\dist\Nava.exe
```

**بررسی سالم بودن صدا روی هر سیستم:**

```bat
dist\Nava.exe --diagnose
```

---

## ۵) سفارشی‌سازی ساخت

| می‌خواهی… | چه کار کنی |
|---|---|
| اسم فایل خروجی عوض شود | در `Nava.spec` خط `name="Nava"` را تغییر بده |
| آیکون عوض شود | فایل `nava.ico` را با آیکون خودت (۲۵۶×۲۵۶) جایگزین کن و `build.bat` را اجرا کن |
| پنجره‌ی کنسول برای دیدن خطاها | در `Nava.spec` مقدار `console=False` را `True` کن |
| حجم کمتر / باز شدن سریع‌تر | حالت *onedir* بساز (پایین) |
| آنتی‌ویروس گیر ندهد | حالت *onedir* معمولاً کم‌مشکل‌تر است |

### حالت onedir (پوشه + exe، باز شدن سریع‌تر)

```bat
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name Nava --icon nava.ico --add-data "nava.ico;." ^
  --hidden-import mutagen.mp3 --hidden-import mutagen.mp4 --hidden-import mutagen.flac ^
  --hidden-import mutagen.oggvorbis --hidden-import mutagen.oggopus --hidden-import mutagen.wave ^
  --hidden-import mutagen.aiff --hidden-import mutagen.asf ^
  --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.Qt3DCore ^
  --exclude-module tkinter --exclude-module unittest ^
  main.py
```

خروجی: `dist\Nava\Nava.exe` (کل پوشه را با هم جابه‌جا کن)

### راه گرافیکی برای مبتدی‌ها

```bat
python -m pip install auto-py-to-exe
auto-py-to-exe
```

Script = `main.py`، حالت **Onefile**، گزینه‌ی **Window Based (hide the console)**، آیکون `nava.ico`، بعد **Convert**.

### یا بگذار گیت‌هاب بسازد

مخزن را روی گیت‌هاب push کن و ورک‌فلوی **Build Windows EXE** را اجرا کن
(*Actions → Build Windows EXE → Run workflow*) — فایل `Nava.exe` در بخش Artifacts آماده است.

---

## ۶) خطاهای رایج و راه حل

| پیام / مشکل | راه حل |
|---|---|
| `'python' is not recognized...` | پایتون را با تیک «Add python.exe to PATH» نصب کن، یا از `py -3` استفاده کن. ترمینال را ببند و باز کن |
| `pip` گیر می‌کند / خطای SSL | `python -m pip install --upgrade pip` و دوباره نصب (VPN/پروکسی را چک کن) |
| `ModuleNotFoundError: PySide6` | `python -m pip install PySide6 mutagen pyinstaller` |
| exe ساخته می‌شود ولی باز نمی‌شود | در `Nava.spec` `console=True` کن، دوباره بساز و از ترمینال اجرا کن تا خطا را ببینی |
| «Failed to execute script» | همان بالا؛ معمولاً یک ماژول جا افتاده و با `--hidden-import` حل می‌شود |
| آنتی‌ویروس exe را قرنطینه می‌کند | False Positive معروف PyInstaller: پوشه را Exception کن یا حالت onedir بساز |
| `Access is denied` | پروژه را جای نوشتنی ببر (نه `C:\Program Files`) و `build`/`dist` قدیمی را پاک کن |
| ساخت کند پیش می‌رود | بار اول طبیعی است (PySide6 بزرگ است)؛ بارهای بعد سریع‌تر |
| `RecursionError` | `python -m pip install --upgrade pyinstaller` و `--noconfirm --clean` |

---

## ۷) بعد از ساخت چه فایل‌هایی ایجاد می‌شود؟

```
C:\nava-player\
├── build\        ← فایل‌های موقت ساخت (قابل حذف)
├── dist\
│   └── Nava.exe  ← 🎯 خروجی نهایی
├── main.py
├── Nava.spec     ← تنظیمات ساخت (اسم، آیکون، کنسول/پنجره‌ای)
├── nava\         ← کد برنامه
└── tools\
```

هر وقت کد را تغییر دادی، فقط `build.bat` را دوباره اجرا کن.
برای تست سریع لازم نیست هر بار exe بسازی؛ `python main.py` فوری اجرا می‌شود.

---

## ۸) چک‌لیست ۳۰ ثانیه‌ای

- [ ] پایتون ۶۴ بیتی نصب است و `python --version` جواب می‌دهد
- [ ] پروژه در مسیر ساده اکسترکت شده (`C:\nava-player`)
- [ ] `python main.py` برنامه را باز می‌کند
- [ ] `build.bat` با پیام `Done!` تمام شد
- [ ] `dist\Nava.exe` باز می‌شود
- [ ] در exe، «Choose folder» آهنگ‌ها را می‌خواند
