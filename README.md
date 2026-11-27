# بررسی سازگاری نیازمندی‌های زمان‌حقیقی

پروژهٔ درس روش‌های رسمی، تیم ۳. ابزار با Python و Z3 می‌سنجد آیا یک رد بولی گسسته در افق تعیین‌شده می‌تواند همهٔ نیازمندی‌ها را ارضا کند. در حالت ناسازگار یک زیرمجموعهٔ ناسازگار کمینه یا MIS گزارش می‌دهد. اجرای پروژه روی CPU است.

## اجرای سریع

Python 3.12 پیشنهاد می‌شود و نسخهٔ آزموده‌شده است.

```bash
python3 -m venv .venv
source .venv/bin/activate
bash setup.sh
bash scripts/run_project.sh demo
bash scripts/run_project.sh test
```

در Windows می‌توانید محیط را با `.venv\Scripts\Activate.ps1` فعال و بسته‌ها را با `python -m pip install -r requirements.txt` نصب کنید. برای تست در PowerShell ابتدا `$env:PYTHONPATH="src"` و سپس `python -m unittest discover -s tests -v` را اجرا کنید.

```bash
python run.py generate --size 60 --mis-size 4 --N 5 --seed 17 --variant varied --output benchmarks/generated/sample.json
python run.py check --input benchmarks/generated/sample.json --method quickxplain
python run.py check --input benchmarks/manual/custom_sat_all_patterns.json
```

مولد با گزینهٔ `--sat` یک نمونهٔ سازگار می‌سازد. گزینهٔ `--style simple` قواعد پس‌زمینهٔ تک‌سیگنالی ایجاد می‌کند. در مثال بررسی، `core` پیش‌فرض است. گزینه‌های `nonincremental`، `incremental` و `quickxplain` مسیرهای دیگر MIS را فعال می‌کنند. `--timeout-ms` مهلت هر پرس‌وجوی CLI است. مطالعهٔ پژوهشی مهلت کل عملیات را نیز اعمال می‌کند.

## خواندن خروجی و مدل

- **SAT** یعنی شاهدی برای همهٔ قواعد در گام‌های ۰ تا N هست.
- **UNSAT** یعنی در مدل محدود هیچ رد سازگاری وجود ندارد.
- **UNKNOWN** یعنی حل‌کننده در شرایط اجرا به تصمیم قطعی نرسیده است.
- **MIS** مجموعه‌ای UNSAT است که با حذف هر عضو SAT می‌شود. یک ورودی می‌تواند چند MIS داشته باشد.
- **Unsat Core** گروهی از قواعد شرکت‌کرده در یک برهان UNSAT است. مسیر `core` آن را با حذف آزمایشی کوچک می‌کند و سپس MIS ارزیابی می‌شود.
- **افزایشی** یعنی قواعد یک‌بار در Z3 رمزگذاری می‌شوند و پرچم‌های فعال‌ساز در هر پرس‌وجو تغییر می‌کنند.

پنج الگو عبارت‌اند از `invariant` برای الزام همیشگی، `absence` برای منع همیشگی، `response` برای پاسخ تا مهلت، `recurrence` برای وقوع در هر پنجره، و `bounded_delay` برای پاسخ بین دو تأخیر. مشاهدات به‌عنوان قیود ثابت محیطی در نظر گرفته می‌شوند. پاسخ باید در افق جا شود و اگر محرک هرگز برقرار نشود، الزام می‌تواند به‌صورت تهی ارضا شود. [معنای رسمی و نمونه‌ها](docs/TEMPORAL_PATTERNS.md)

## آزمایش و بازتولید

```bash
bash scripts/run_project.sh pilot
bash scripts/run_project.sh full
python analysis/analyze_results.py --study results/final
```

فرمان `full` تنظیمات از پیش ثبت‌شده را اجرا و خروجی را در `results/reproduced-final/` می‌نویسد. اجرای همان فرمان و همان مقصد بعد از وقفه از رکوردهای تکمیل‌شده استفاده می‌کند. روی محیط متفاوت یک مقصد تازه انتخاب کنید. برای Colab از [نوت‌بوک](notebooks/FINAL_COLAB.ipynb) با ZIP استخراج‌شده یا نسخهٔ موجود در GitHub استفاده کنید. [جزئیات بازتولید](docs/REPRODUCIBILITY.md)

### اجرا در Google Colab

1. [نوت‌بوک شاخهٔ انتشار](https://colab.research.google.com/github/Ehsan-Rezaeii/realtime-requirements-mis/blob/final-project-completion/notebooks/FINAL_COLAB.ipynb) را باز کنید. از **Runtime → Change runtime type**، گزینهٔ **CPU** را انتخاب کنید.
2. **Runtime → Run all** را بزنید. نوت‌بوک نسخهٔ شاخهٔ انتشار را دریافت می‌کند و پس از نصب وابستگی‌ها Demo، تست‌ها، پایلوت و نمودارهای پایلوت را اجرا می‌کند.
3. مقدار `RUN_FULL` پیش‌فرض `False` است. برای اجرای کامل آن را `True` کنید و سلول «اجرای اصلی» و سلول‌های بعد را دوباره اجرا کنید. برای ذخیره در Drive، پیش از پایلوت `SAVE_TO_DRIVE = True` بگذارید.
4. برای شاخه، تگ یا کامیت دیگری، یک سلول کد پیش از نخستین سلول کد اضافه کنید و `%env TEAM3_REF=نام_شاخه_یا_تگ_یا_شناسه_کامل_کامیت` را اجرا کنید. نوت‌بوک نسخه را در پوشهٔ کاری جدا باز می‌کند.

**اجرا از ZIP**. ZIP را در Colab بارگذاری و استخراج کنید. در سلولی پیش از کد راه‌اندازی، `%env TEAM3_PROJECT=/content/realtime-requirements-mis` را با مسیر واقعی پوشهٔ دارای `setup.sh` اجرا کنید. اگر قبلاً `TEAM3_REF` را تنظیم کرده‌اید، با `os.environ.pop("TEAM3_REF", None)` پس از `import os` آن را پاک کنید. نصب وابستگی‌ها همچنان به PyPI دسترسی می‌خواهد.

| پوشه | محتوا |
|---|---|
| `src/team3fm` | مدل، حل‌کننده، استخراج، مولد و CLI |
| `benchmarks` | ورودی‌های دستی، مصنوعی پایه و عمومی، جدول منشأ |
| `experiments` | تنظیمات پایلوت، مطالعهٔ اصلی و پایلوت تاریخی |
| `results/final` | دادهٔ خام، جدول‌ها، نمودارها، مانیفست و گزارش محیط |
| `results/archive` | یادداشت منشأ اجراهای Windows و بایگانی محلی |
| `analysis`، `scripts`، `tests` | تحلیل، اعتبارسنج مستقل، نصب و آزمون‌ها |
| `docs`، `reports` | مستندات فارسی، گزارش فنی و مواد دفاع |

اندازه‌گیری‌ها نشان دادند استفادهٔ مجدد از حل‌کننده در دسته‌های چند پرس‌وجویی رمزگذاری را ارزان‌تر می‌کند. در استخراج، Core و QuickXplain با تعداد فراخوانی کمتری روی خانوادهٔ بزرگ قابل مقایسه‌اند. آزمایش افق یک ناسازگاری با ورود رخداد و یک سازگاری پس از فراهم شدن گام پاسخ نشان می‌دهد. شمار موفقیت، timeout و اندازهٔ MIS در گزارش آمده است. نتیجه‌ها محدود به مدل بولی کراندار و مجموعه‌های انتخاب‌شده‌اند. [گزارش فنی](reports/FINAL_REPORT_FA.md) · [نسخهٔ PDF](reports/FINAL_REPORT_FA.pdf) · [تحویل و وضعیت الزامات](FINAL_HANDOFF.md)
