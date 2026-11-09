# Real-Time Requirements MIS

بررسی سازگاری نیازمندی‌های زمانی و استخراج زیرمجموعه ناسازگار کمینه (MIS) با Python و Z3.

## نصب و اجرا

Python 3.9 یا جدیدتر لازم است. دستورها را در پوشه اصلی پروژه اجرا کنید:

```bash
python -m pip install -r requirements.txt
python run.py demo
```

برای اجرای تست‌ها:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

در Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## داده و بررسی سازگاری

ورودی‌های نمونه در `benchmarks/pilot/` قرار دارند. برای ساخت ورودی جدید و بررسی آن:

```bash
python run.py generate --size 30 --mis-size 3 --style mixed --N 5 --seed 42 --output benchmarks/generated/my_case.json
python run.py check --input benchmarks/generated/my_case.json --method core
python run.py check --input benchmarks/pilot/mixed_mis3_30.json --method incremental
```

روش‌های موجود: `nonincremental`، `incremental` و `core` (Unsat Core همراه با حذف تکراری). هر روش یک MIS پیدا می‌کند؛ حذف هر عضو آن باید مجموعه را سازگار کند. MIS الزاماً کوچک‌ترین مجموعه از نظر تعداد اعضا نیست و Unsat Core نیز الزاماً کمینه نیست.

فرمت ورودی:

```json
{
  "case_id": "example",
  "N": 5,
  "rules": [
    {"id": "R1", "type": "invariant", "signal": "alarm"},
    {"id": "R2", "type": "absence", "signal": "alarm"}
  ]
}
```

زمان گسسته و شامل نقاط `0` تا `N` است. سیگنال‌ها بولی‌اند. الگوهای پشتیبانی‌شده:

- `invariant`: سیگنال در همه گام‌ها درست است.
- `absence`: سیگنال در همه گام‌ها نادرست است.
- `response`: پس از رخداد `trigger`، سیگنال `target` از همان لحظه تا `deadline` گام بعد و درون افق رخ می‌دهد.
- `recurrence`: در هر پنجره کامل با طول `window` دست‌کم یک رخداد وجود دارد.
- `bounded_delay`: پاسخ بین `min_delay` و `max_delay` گام بعد و درون افق رخ می‌دهد؛ اگر زمان مجازی باقی نماند، رخداد محرک ناممکن است.

فیلد اختیاری `observations` مشاهده‌های ثابت محیطی است، مانند `{"signal":"request","time":3,"value":true}`؛ این مشاهده‌ها عضو MIS نیستند. فیلدهای `seed` و `injected_ids` نیز اختیاری‌اند.

## آزمایش و نمودار

پارامترهای آزمایش در `experiments/config.json` هستند:

```bash
python run.py benchmark --mode all --config experiments/config.json
python analysis/plot_results.py --input results/generated/rq1_consistency.csv --output analysis/figures/rq1.png
python analysis/plot_results.py --input results/generated/rq2_rq3_rq5_mis.csv --output analysis/figures/rq5.png
```

حالت‌های `consistency`، `mis` و `bounds` را می‌توان جدا اجرا کرد. خروجی‌های CSV و مشخصات محیط در `results/generated/` ساخته می‌شوند. اجرای مجدد، فایل‌های هم‌نام را بازنویسی می‌کند. خروجی‌ها و نمودارهای تولیدشده در Git ثبت نمی‌شوند.

زمان‌سنجی شامل ساخت حل‌کننده و حل مسئله است؛ اعتبارسنجی MIS جدا انجام می‌شود. `timeout_ms` محدودیت هر فراخوانی Z3 است. پاسخ `unknown` به معنای SAT یا UNSAT نیست.

داده‌ها مصنوعی‌اند و تغییر seed فقط ترتیب قوانین را تغییر می‌دهد. ناسازگاری در انتهای افق می‌تواند ناشی از قرارداد `bounded_delay` باشد. در سناریوی `late_conflict` آزمایش کران، مشاهده زمان ۳ فقط برای `N >= 3` اضافه می‌شود. نتایج آزمایش‌ها تضمین برتری عمومی یک روش نیستند.

## ساختار

```text
src/team3fm/              # مدل، حل‌کننده، MIS، مولد داده و CLI
tests/                   # تست‌های صحت و آزمایش‌ها
benchmarks/pilot/         # ورودی‌های نمونه JSON
experiments/config.json  # تنظیمات آزمایش
analysis/plot_results.py # رسم نمودار از CSV
run.py                   # نقطه ورود اجرا
pyproject.toml           # تنظیمات بسته Python
requirements.txt         # وابستگی‌های اجرا و نمودار
```
