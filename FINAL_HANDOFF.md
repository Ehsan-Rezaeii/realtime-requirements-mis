# تحویل نهایی پروژهٔ روش‌های رسمی، تیم ۳

## A. وضعیت

**PARTIAL در تطابق با راهنمای درس.** نسخهٔ محلی تحویل شامل کد آزموده، همهٔ آزمایش‌های CPU برنامه‌ریزی‌شده، نتایج خام، تحلیل خودکار، گزارش فارسی، ZIP بازتولید و مواد دفاع است. مقایسهٔ زمانی خارجی روی یک مسئلهٔ هم‌معنا، اندازهٔ مجموعهٔ عمومیِ قابل تبدیل و آزمون در سرویس واقعی Colab باز هستند. شواهد پایلوت معیار فنی داخلی را پوشش دادند. تصمیم رسمی استاد و پذیرش مقایسهٔ جایگزین در اختیار تیم درس است.

## B. تغییرات و تصمیم‌های فنی

- `model.py` و `solver.py` زمان ۰ تا N و مشاهدات ثابت را حفظ می‌کنند. فضای نام فعال‌سازی از سیگنال جدا شد.
- `mis.py` سه روش حذف و Core و روش QuickXplain را در اختیار می‌گذارد. اعتبارسنجی عضویت، UNSAT و SAT بعد از حذف هر عضو را بررسی می‌کند.
- `generator.py` ورودی SAT و گونهٔ varied را اضافه کرد. گونهٔ کلاسیک و مسیر benchmark قدیمی برای بازتولید اولیه حفظ شده‌اند.
- `study.py`، worker جدا و تنظیمات `final.json` بودجهٔ کل، ثبت چرخشی، هش ورودی و ادامه از رکورد ذخیره‌شده را فراهم می‌کنند.
- ارزیاب مستقیم رد، دو آزمون خارجی، مستندات فارسی، نوت‌بوک، گردش‌کار آزمون و اسکریپت رسم اضافه شدند. [جزئیات تغییر](docs/CHANGELOG.md)

## C. آزمون‌ها

۲۵ تست اجرا و موفق شدند. شکست و تست اجرا‌نشده در مجموعهٔ کشف‌شده صفر بود. نصب در venv تازه روی Linux، Demo و اجرای سلول‌های نوت‌بوک در Jupyter محلی کنترل شدند. ارزیاب مستقل ۳۲۹ کنترل موفق، ۰ اختلاف و ۰ کنترل با وضعیت `not_checked` ثبت کرد. هفت ردیف اطلاعاتی دربارهٔ موارد دارای اجرای غیرموفق در CSV وجود دارد و جزء شمار کنترل منطقی نیست. [تست‌ها](results/validation/test_log.txt) · [نصب تازه](results/validation/clean_install_log.txt) · [نوت‌بوک Linux](results/validation/notebook_linux_log.txt) · [راستی‌آزمایی مستقل](results/validation/independent_validation.csv)

## D. آزمایش‌ها

۵۸ ورودی متمایز شامل ۳۰ مورد برای RQ1/RQ2/RQ3/RQ5 و ۲۸ ترکیب سناریو و افق برای RQ4 به کار رفت. ۲٬۳۶۰ اجرا با ۱۰ تکرار انجام شد. ۲٬۲۵۰ موفق، ۱۱۰ timeout و صفر UNKNOWN، crash، error، invalid یا not_run ثبت شد. در ۷۴۴ اجرا یک MIS معتبر گزارش شد. این شمار شامل تکرار یک ورودی با روش‌ها و تکرارهای مختلف است. [آمار وضعیت](results/final/summary/run_status.csv) · [خلاصهٔ ماشینی](results/final/summary/report_snapshot.json)

## E. یافته‌ها

| پرسش | نتیجهٔ مستقیم |
|---|---|
| RQ1 | در دسته‌های Mixed با جفت موفق، افزایشی به میانهٔ ۱٫۷۰ تا ۳٫۱۷ برابر رسید. در ۵٬۰۰۰ قید، افزایشی ۶ تلاش موفق و مبنای تازه صفر داشت. |
| RQ2 | در ۶۰ قید Mixed، روش Core با میانهٔ حدود ۳۴٫۷ میلی‌ثانیه و چهار فراخوانی Z3 یک MIS سه‌عضوی استخراج کرد. حذف تازه و حذف افزایشی ۶۱ فراخوانی داشتند. |
| RQ3 | هر ۷۴۴ نامزد با بررسی قطعی معتبر و کمینه بود. Core در هر ۱۶ مورد مصنوعی تزریقی دست‌کم یک بار هستهٔ دقیق را پیدا کرد. |
| RQ4 | مشاهدهٔ گام ۳، late conflict را از همان افق آشکار کرد. در مثال مرزی، تأخیر مثبت با N=2 یا N=3 در افق جا نمی‌شد و در N=4 جواب SAT شد. |
| RQ5 | در ۵٬۰۰۰ قید، Core در ۸ از ۱۰ تلاش موفق شد. سه روش دیگر در آن اندازه به سقف زمان رسیدند. در ۲٬۰۰۰ قید، Core و QuickXplain هر دو ۱۰ موفقیت داشتند. |

پایلوت داخلی افزایشی را در ۴ از ۴ و Core را در ۳ از ۴ مورد مصنوعی سریع‌تر یا هم‌سطح با قوی‌ترین baseline داخلی نشان داد. تصمیم فنی محلی برای ادامه مناسب بود. آزمون Wilcoxon روی پنج ورودی مصنوعی ۳۰ قیدی اکتشافی است. مقایسه‌های اصلاح‌شدهٔ Holm در این نمونه شواهد کافی برای ادعای معناداری کلی ندادند. [جفت‌ها و سرعت](results/final/summary/paired_speedups.csv) · [آمار اکتشافی](results/final/summary/paired_inference.csv) · [پایلوت](results/pilot/summary/pilot_gate.csv)

## F. اقلام تحویل

| مورد | محل |
|---|---|
| کد، CLI، تست‌ها | `src/team3fm/`، `run.py`، `tests/` |
| مولد و ورودی‌ها | [مانیفست](benchmarks/manifest.csv)، `benchmarks/manual/`، `benchmarks/public/` |
| طرح و ثبت محیط | [آزمایش](docs/EXPERIMENT_GUIDE.md)، [محیط](results/final/environment.json) |
| دادهٔ خام و تحلیل | `results/final/raw/`، `results/final/summary/`، `results/final/figures/` |
| بایگانی نفر دوم | [یادداشت منشأ و بایگانی محلی](results/archive/README.md) |
| اعتبارسنجی و Baseline خارجی | [گزارش](docs/VALIDATION_REPORT.md)، [مبناها](docs/BASELINE_VERIFICATION.md) |
| نصب و Notebook | `setup.sh`، `scripts/run_project.sh`، [نوت‌بوک](notebooks/FINAL_COLAB.ipynb) |
| گزارش و PDF | [متن](reports/FINAL_REPORT_FA.md) و [PDF](reports/FINAL_REPORT_FA.pdf) |
| دفاع و مواد ارائه | [دفاع](reports/DEFENSE_GUIDE_FA.md)، [مواد اولیه](reports/PRESENTATION_SOURCE_FA.md) |
| کنترل کیفیت | [چک‌لیست](docs/REQUIREMENTS_CHECKLIST.md)، [محدودیت‌ها](docs/LIMITATIONS.md) |

## G. بازتولید

```bash
bash setup.sh
bash scripts/run_project.sh demo
bash scripts/run_project.sh test
bash scripts/run_project.sh pilot
bash scripts/run_project.sh full
python analysis/analyze_results.py --study results/final
python analysis/update_report.py
```

اجرای مجدد مطالعه به‌صورت پیش‌فرض در `results/reproduced-*` ثبت می‌شود. برای تولید گزارش از اجرای تازه، `--study`، `--pilot` و `--validation` را به مسیرهای همان اجرای تازه بدهید. [جزئیات](docs/REPRODUCIBILITY.md)

## H. موارد باز

FRET فرمول زمانی بومی را داد و Hanfor دو چک مشترک بولی را گذراند. Ultimate ReqAnalyzer اجرا نشد و مقایسهٔ زمان بین‌ابزاری هم‌معنا انجام نشد. چهار قید نماینده از دو منبع عمومی منتقل شدند. برای ارزیابی صنعتی به زبان و دادهٔ گسترده‌تر نیاز است. نوت‌بوک در Jupyter/Linux اعتبارسنجی شد و اجرای میزبانی Colab و Drive باقی است. MARCO در دامنهٔ اختیاری شمارش است. [چک‌لیست وضعیت](docs/REQUIREMENTS_CHECKLIST.md)

## I. Git

شاخهٔ محلی `final-project-completion` از `3e39bc8a7baa9786147bff38e1ebb3f8c301561b` ساخته شد. کد مولد شواهد نهایی در `4301d213b3c06dbce7759fed39a2c77273757664` ثبت شد. شناسهٔ سر شاخهٔ تحویل با `git rev-parse HEAD` در مخزن یا `DELIVERY_COMMIT.txt` در ZIP مشخص می‌شود. وضعیت Git هنگام اجرای مطالعهٔ اصلی پاک بود. شاخهٔ انتشار از مبنای اصلی با فایل‌های مجاز ساخته شد. نسخهٔ محلی ممیزی‌شده در کامیت `c3de51a` برقرار است. انتشار صرفاً در شاخهٔ `final-project-completion` و با PR انجام می‌شود. ادغام به تأیید کاربر وابسته است.
