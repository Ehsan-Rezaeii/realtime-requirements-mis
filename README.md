# پروژه تیم ۳ — روش‌های رسمی

**Real-Time Requirements Consistency Checking & Minimal Inconsistent Subset (MIS) Extraction**

پروژه دانشگاهی ساده و قابل اجرا روی **Google Colab (CPU)**؛ بدون نیاز به LLM، API پولی یا GPU. زبان **Python** و حل‌کننده **Z3** است.

> **وضعیت:** نسخه یکپارچه MVP/Pilot. این ریپو «نتایج نهایی همه RQها» یا برتری تضمین‌شده یک روش را ادعا نمی‌کند. گزارش نتایج باید فقط از اجراهای واقعی ساخته شود. خروجی‌های `results/pilot/` از آزمایش‌های قبلی تیم آمده‌اند و بازتولید خودکار آن‌ها با همین نسخه کد هنوز باید در Colab بررسی شود.

## ۱) اجرای سریع در Google Colab

اگر هنوز در GitHub آپلود نکرده‌اید، فایل ZIP پروژه را از حالت فشرده خارج کنید و پوشه را در Colab/Drive قرار دهید. پس از انتشار ریپو، راحت‌ترین روش در یک Notebook جدید:

```python
# CELL 1: replace USERNAME/REPO with the actual public repository URL
!git clone https://github.com/USERNAME/REPO.git
%cd REPO

# CELL 2
%pip install -r requirements.txt

# CELL 3: simple SAT/UNSAT and MIS example
!python run.py demo

# CELL 4: full unit tests (requires z3-solver)
!PYTHONPATH=src python -m unittest discover -s tests -v
```

در صورت ریست شدن Runtime، نصب کتابخانه و اجرای سلول‌ها باید تکرار شود؛ خود فایل‌ها در GitHub باقی می‌مانند. اجرای سلول‌ها در نوت‌بوک `notebooks/quickstart.ipynb` هم نمونه‌سازی شده است.

## ۲) اجرا روی کامپیوتر

با Python و Git نصب‌شده، در پوشه پروژه دستورهای زیر را اجرا کنید:

```bash
python -m pip install -r requirements.txt
python run.py demo
PYTHONPATH=src python -m unittest discover -s tests -v
```

در Windows PowerShell برای اجرای تست از این دستور استفاده کنید:

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

یا در Linux/Colab می‌توانید `bash setup.sh` را برای نصب کتابخانه‌ها اجرا کنید.

## ۳) روش‌های پیاده‌سازی‌شده

- `Non-Incremental`: برای هر بررسی، Solver جدید ساخته می‌شود.
- `Incremental`: قوانین یک‌بار رمزگذاری می‌شوند و با assumption literals فعال/غیرفعال می‌شوند.
- `Core+Deletion`: ابتدا `unsat_core` می‌گیرد و بعد آن را با حذف تکراری کمینه می‌کند.

هر سه روش، **یک** MIS تولید می‌کنند. کمینگی با این دو شرط تأیید می‌شود: کل MIS باید `UNSAT` باشد و با حذف هر عضو باید `SAT` شود. `Unsat Core` به تنهایی الزاماً MIS نیست.

## ۴) کار با فایل‌های JSON

برای ساخت مجموعه ۳۰ قانونی با سه قانون ناسازگار:

```bash
python run.py generate --size 30 --mis-size 3 --style mixed --N 5 --seed 42 --output benchmarks/generated/my_case.json
```

برای بررسی فایل آماده‌شده توسط نفر دوم:

```bash
python run.py check --input benchmarks/pilot/mixed_mis3_30.json --method core
python run.py check --input benchmarks/generated/my_case.json --method incremental
```

نمونه فرمت:

```json
{
  "case_id": "example",
  "N": 5,
  "rules": [
    {"id":"R1", "type":"invariant", "signal":"alarm"},
    {"id":"R2", "type":"absence", "signal":"alarm"}
  ]
}
```

فیلدهای اختیاری: `seed`، `injected_ids` و `observations` (مشاهده ثابت در زمان مشخص). تعریف دقیق الگوها و محدودیت افق زمانی در [docs/model_semantics.md](docs/model_semantics.md) آمده است.

## ۵) آزمایش‌ها و خروجی خام

پارامترها در `experiments/config.json` هستند؛ تعداد قوانین (`sizes`)، `N`، تکرار، seed، `timeout_ms` و پوشه خروجی را می‌توان تغییر داد. **ابتدا با مقادیر کوچک** شروع کنید.

```bash
python run.py benchmark --mode all --config experiments/config.json
```

برای اجرای جداگانه:

```bash
python run.py benchmark --mode consistency --config experiments/config.json
python run.py benchmark --mode mis --config experiments/config.json
python run.py benchmark --mode bounds --config experiments/config.json
```

این دستورها در `results/generated/` فایل‌های زیر را ایجاد می‌کنند:

| فایل | کارکرد |
|---|---|
| `rq1_consistency.csv` | RQ1: زمان بررسی سازگاری افزایشی و غیرافزایشی روی زیرمجموعه‌های یکسان |
| `rq2_rq3_rq5_mis.csv` | RQ2، RQ3، RQ5: زمان، اندازه و کمینگی MIS و اثر تعداد قوانین |
| `rq4_bound_effect.csv` | RQ4: اثر کران `N` بر SAT/UNSAT در سه سناریوی پایه |
| `environment.json` | نسخه Python و Z3، سیستم‌عامل، seed، timeout و پیکربندی |

هر نتیجه به‌محض اتمام در CSV اضافه می‌شود. اجرای مجدد هر دستور **خروجی با همان نام را بازنویسی می‌کند**؛ قبل از آزمایش جدید فایل خام قبلی را آرشیو کنید. `unknown` و `error` جدا ثبت می‌شوند. محدودیت timeout برای هر `check()` است، نه کل عملیات.

**نمودارهای نفر سوم (از CSV واقعی):**

```bash
python analysis/plot_results.py --input results/generated/rq1_consistency.csv --output analysis/figures/rq1.png
python analysis/plot_results.py --input results/generated/rq2_rq3_rq5_mis.csv --output analysis/figures/rq5.png
```

برای تحلیل داده‌های Pilot قدیمی، فایل‌های `results/pilot/` را بدون دست‌کاری نگه دارید.

## ۶) ساختار پوشه‌ها

```text
team3_formal_methods/
├── src/team3fm/              # model, solver, MIS, generator, experiments, CLI
├── tests/                    # unit tests, correctness and boundary tests
├── benchmarks/pilot/         # JSON datasets already supplied by the team
├── benchmarks/generated/     # new local inputs (ignored by Git)
├── experiments/config.json   # all pilot settings in one place
├── results/pilot/            # original raw CSV/JSON pilot files
├── results/generated/        # future raw results (ignored by Git)
├── analysis/plot_results.py  # charts from real experiment CSVs
├── docs/                     # model semantics, team workflow, caveats
├── notebooks/quickstart.ipynb
├── run.py                    # single command-line entry point
├── setup.sh
├── requirements.txt
└── README.md
```

## ۷) تقسیم کار تیم

**نفر اول، Developer:** نگهداری کد `src/` و تست‌های `tests/`، رفع خطا و آموزش اجرا. **نفر دوم، Data & Experimenter:** داده‌های متنوع‌تر، اجرای آزمایش‌ها و نگهداری نتایج خام و تنظیمات. **نفر سوم، Analyst & Presenter:** اعتبارسنجی مستقل، نمودارهای مبتنی بر داده واقعی، گزارش و پاورپوینت. هر سه نفر باید بتوانند `demo` را اجرا و SAT/UNSAT/MIS را توضیح دهند. جزئیات همکاری: [docs/team_workflow.md](docs/team_workflow.md).

## ۸) انتشار در GitHub — توسط صاحب حساب

**نکته:** این بسته هنوز به حساب GitHub شما متصل نشده و هیچ ریپوی عمومی ایجاد نشده است. در GitHub یک ریپوی جدید مثلاً `team3-formal-methods` بسازید، وضعیت آن را `Public` قرار دهید و هنگام ایجاد ریپو `README` اولیه جداگانه نسازید تا با فایل این پروژه تداخل ایجاد نشود. بعد در ترمینال داخل پوشه پروژه:

```bash
git init
git add .
git commit -m "Initial integrated Team 3 MVP"
git branch -M main
git remote add origin https://github.com/USERNAME/team3-formal-methods.git
git push -u origin main
```

`USERNAME` را با نام واقعی حساب GitHub خود عوض کنید. در GitHub برای ویرایش مشترک باید اعضای تیم را به‌عنوان Collaborator دعوت کنید؛ عمومی بودن ریپو فقط اجازه دیدن آن را به همه می‌دهد. بهتر است اعضا در شاخه‌های جدا کار کنند و با Pull Request تغییرات را ادغام کنند. راهنمای پروژه استاد یا فایل خصوصی را بدون اجازه در ریپوی عمومی منتشر نکنید.

## ۹) محدودیت‌ها و کارهای بعدی

- آزمایش‌های موجود عمدتاً روی داده مصنوعی ساده‌اند. تغییر seed در مولد کنونی **فقط ترتیب قوانین را تغییر می‌دهد**، نه محتوای منطقی را؛ بنابراین چند seed لزوماً چند بنچمارک مستقل نمی‌سازد.
- سناریوهای وابسته به مرز `N` و مدل پاسخ زمانی را باید در گزارش به‌وضوح توضیح داد.
- بنچمارک عمومی معتبر، آزمایش روی مقیاس بزرگ‌تر، بررسی FRET/Hanfor و تصمیم درباره QuickXplain/MARCO هنوز نیازمند بررسی‌اند. این بسته آن‌ها را پیاده‌سازی‌شده معرفی نمی‌کند.
- آزمایش‌های کامل RQ1 تا RQ5، تکرارپذیری، تحلیل مستقل و پاورپوینت نهایی وظیفه مشترک تیم هستند.
- **مهم:** بسته کنونی برای استفاده عملی در Colab آماده‌سازی شده است، اما تست اجرای واقعی Z3 روی این نسخه یکپارچه باید در محیطی با `z3-solver` نصب‌شده انجام شود. موفقیت تست‌های Notebook قبلی به‌تنهایی تضمین نمی‌کند این نسخه جدید بدون خطا باشد.

**منبع روش پروژه:** راهنمای استاد، بخش عمومی و قسمت تیم ۳. فایل Word استاد عمداً داخل این ریپوی عمومی قرار داده نشده است.

یادداشت مهم درباره تفاوت زمان‌سنجی‌های قدیمی: [docs/pilot_notes.md](docs/pilot_notes.md).

## ۱۰) تست خودکار روی GitHub

فایل `.github/workflows/tests.yml` بعد از `push` یا ایجاد Pull Request، تست‌های Python/Z3 را در GitHub Actions اجرا می‌کند. پس از آپلود، برگه **Actions** ریپو را بررسی کنید. سبز شدن تست‌ها نشانه موفقیت آزمون‌های خودکار در آن محیط است؛ جایگزین تأیید علمی کل پروژه نیست. اگر Actions شکست خورد، متن کامل خطا را ثبت و اصلاح کنید.
