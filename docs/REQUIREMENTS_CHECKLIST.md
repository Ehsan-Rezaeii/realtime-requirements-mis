# وضعیت الزامات و شواهد

| الزام یا کنترل | وضعیت | مسیر شاهد و توضیح |
|---|---|---|
| مطالعهٔ راهنمای مشترک، بخش تیم ۳ و پیوست ارزیابی | PASS | [ممیزی](INITIAL_AUDIT.md)، [طرح مطالعه](EXPERIMENT_GUIDE.md) |
| مدل گسسته و پنج الگو | PASS | [الگوها](TEMPORAL_PATTERNS.md)، `src/team3fm/model.py`، [تست](../results/validation/test_log.txt) |
| حل افزایشی و غیرافزایشی | PASS | `solver.py`، [RQ1 خام](../results/final/raw/rq1_consistency.csv) |
| حذف تازه، حذف افزایشی، Core کوچک‌شده، QuickXplain | PASS | `mis.py`، [جدول زمان و اندازه](../results/final/summary/rq2_mis_timing_and_size.csv) |
| تفکیک Core و MIS و کنترل عضویت و کمینگی | PASS | [روش](METHODOLOGY.md)، [RQ3](../results/final/summary/rq3_correctness.csv) |
| شمارش MIS با MARCO | NOT APPLICABLE | در جدول استاد اختیاری است. مخزن بررسی شد و دامنهٔ این مطالعه استخراج یک MIS است. [مبناها](BASELINE_VERIFICATION.md) |
| آزمون خودکار و لاگ تعداد | PASS | [۲۵ تست](../results/validation/test_log.txt)، [نصب تازه](../results/validation/clean_install_log.txt) |
| اعتبارسنج مستقل | PASS | [روش](VALIDATION_REPORT.md)، [CSV](../results/validation/independent_validation.csv) |
| دادهٔ SAT و UNSAT، دستی و تزریقی ۲ تا ۴ | PASS | [مانیفست](../benchmarks/manifest.csv)، [مانیفست اجرا](../results/final/case_manifest.csv) |
| دادهٔ عمومی، منبع، مجوز و محدودیت انتقال | PASS | [دو زیرمجموعه](DATASET_GUIDE.md)، فایل‌های اصلی در `benchmarks/public/source` |
| مجموعهٔ عمومیِ تبدیل‌شده در مقیاس ده‌ها یا صدها قید | PARTIAL | زیرمجموعه‌های قابل بیان کوچک‌اند. مجموعهٔ ۹۷ قیدی Lockheed Martin بررسی شد. [معیار گزینش](DATASET_GUIDE.md) |
| اجرای خارجی FRET و Hanfor و اعلام نسخه | PASS | [تولید فرمول و شبیه‌سازی](BASELINE_VERIFICATION.md)، [شاهد مشترک Hanfor](../results/validation/hanfor_shared_subset.csv) |
| مقایسهٔ end-to-end با ابزار خارجی روی بودجه و مسئلهٔ همسان | PARTIAL | UReqCheck دریافت نشد و معناشناسی FRET متفاوت است. دو چک منطقی Hanfor و روش‌های داخلی هم‌معنا ثبت شده‌اند. تأیید جایگزین با استاد است. [شواهد](BASELINE_VERIFICATION.md) |
| RQ1 سرعت دسته و زمان ساخت/حل | PASS | [جدول](../results/final/summary/rq1_timing.csv) و [نمودار](../results/final/figures/rq1_consistency.svg) |
| RQ2 زمان و اندازهٔ خروجی، تعداد فراخوانی | PASS | [جدول](../results/final/summary/rq2_mis_timing_and_size.csv) |
| RQ3 درستی، کمینگی و تزریق | PASS | [جدول](../results/final/summary/rq3_correctness.csv) |
| RQ4 افق، مشاهدهٔ دیرهنگام و اثر مرزی | PASS | [وضعیت](../results/final/summary/rq4_status.csv) و [نمودار](../results/final/figures/rq4_bound_timing.svg) |
| RQ5 مقایسهٔ بودجه‌دار تا ۵٬۰۰۰ | PASS | [موفقیت و توقف](../results/final/summary/rq5_scalability.csv)، [نمودار](../results/final/figures/rq5_status.svg) |
| آزمون اختیاری ۱۰٬۰۰۰ قید | PASS | [دو اجرای Core](../results/validation/stress_10000_log.txt)، به‌صورت جدا از مقایسه |
| تعداد تکرار و seed و ثبت محیط و commit | PASS | [محیط و تنظیمات](../results/final/environment.json)، [مانیفست اجرا](../results/final/experiment_manifest.csv) |
| مهلت Z3 و مهلت کل، UNKNOWN، خطا، crash و resume | PASS | [آزمون‌ها](../results/validation/test_log.txt)، [وضعیت اجرا](../results/final/summary/run_status.csv)، [شکست‌ها](../results/final/logs/failures.csv) |
| حفظ داده‌های خام و اجرای قبلی | PASS | [بایگانی](../results/archive/README.md)، [خام نهایی](../results/final/raw/)، [پایلوت جدید](../results/pilot/raw/) |
| تولید خودکار جدول، نمودار و آزمون آماری | PASS | [تحلیل](../analysis/README.md)، [آمار جفت‌شده](../results/final/summary/paired_inference.csv) |
| محدودیت سخت‌افزار، مدل و دامنهٔ داده | PASS | [محدودیت‌ها](LIMITATIONS.md)، [گزارش فارسی](../reports/FINAL_REPORT_FA.md) |
| نصب تازه و اجرای سریع CPU | PASS | [لاگ](../results/validation/clean_install_log.txt)، `setup.sh`، `scripts/run_project.sh` |
| Notebook بازتولید و آزمون Jupyter/Linux | PASS | [نوت‌بوک](../notebooks/FINAL_COLAB.ipynb)، [لاگ](../results/validation/notebook_linux_log.txt) |
| اجرای Notebook در سرویس Google Colab | NOT RUN | اعتبارسنجی محلی Linux و مسیر ZIP انجام شد. mount و runtime میزبانی Google به جلسهٔ Colab نیاز دارد. |
| گزارش فارسی، PDF و راهنمای یک‌فرمانی | PASS | [گزارش](../reports/FINAL_REPORT_FA.md)، [PDF](../reports/FINAL_REPORT_FA.pdf)، [راهنما](../README.md) |
| مواد پاورپوینت و دفاع | PASS | [مواد اولیه](../reports/PRESENTATION_SOURCE_FA.md)، [دفاع](../reports/DEFENSE_GUIDE_FA.md) |
| تصمیم فنی پایلوت با شاهد مستقل | PASS | [مقایسه](../results/pilot/summary/pilot_gate.csv)، [شاهد مستقل](../results/validation/pilot_validation.csv) |
| تصمیم رسمی Go/No-Go | NOT RUN | جلسه با استاد در این اجرا برگزار نشد. |
| حفظ حریم خصوصی و شاخهٔ اصلی | PASS | شاخهٔ محلی مستقل. بستهٔ نهایی فاقد فایل خصوصیِ راهنمای استاد و فایل احراز هویت است. |
| پایلوت داخل Docker | NOT APPLICABLE | نصب اصلی مطابق راهنمای منابع محدود با `setup.sh` و پردازش CPU انجام شد. Docker وابستگی بازتولید Colab نیست. |
