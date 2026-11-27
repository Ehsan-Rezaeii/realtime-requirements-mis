# اجرای مبناها و ابزارهای خارجی

| روش یا ابزار | نسخه و نتیجهٔ آزمون | دامنهٔ مقایسه |
|---|---|---|
| Z3 با حل‌کنندهٔ تازه | Python package `4.15.4.0`، Z3 `4.15.4`. اجرا در پایلوت و مطالعهٔ اصلی | مبنای اصلی RQ1 و حذف تکراری RQ2 |
| Z3 با assumptions | همان نسخه و ورودی‌ها | بررسی دسته‌ای افزایشی و حذف با حل‌کنندهٔ مشترک |
| Unsat Core و حذف | همان Z3، ثبت اندازهٔ Core و MIS و بررسی حذف همهٔ اعضا | روش پیشنهادی استخراج |
| QuickXplain | پیاده‌سازی Python این مخزن از تقسیم بازگشتی Junker | آزموده با موارد ۲ تا ۴ عضو و یک مورد چند MIS |
| MARCO | منبع رسمی و commit در دسترس، هدف شمارش چند MUS/MCS | اختیاری به تصریح جدول استاد. وضعیت اجرا برای این مطالعه N/A است. |
| FRET | `v3.1.0`، commit `58db455be35182a015e607232d9f4e3c86731932`. CLI دو فرمول متناهی را تولید کرد. | بررسی ترجمه روی نمونهٔ عمومی. مقایسهٔ زمانی هم‌معنا در دسترس قرار نگرفت. |
| Hanfor | `v1.2.1`، commit `fbfa344beb5b1f81f61b6b1c4b05b6369f0af1f8`. CLI راه‌اندازی شد و simulator دو نمونهٔ مشترک را بررسی کرد. | توافق منطقی روی دو الگوی سراسری. اجرای واقعی Ultimate ReqAnalyzer انجام نشد. |

## نتیجهٔ FRET

با Node 24 و npm 11، تنظیم devEngines نسخهٔ قدیمی پذیرفته نشد. Node 20.19.0 و npm 10.8.2 با وابستگی‌های قفل‌شدهٔ ریشه و پوشهٔ app برای ساخت CLI به کار رفتند. دستور `npm run --silent start-cli -- formalize -l ft-fin '<FRETish>'` برای هر دو ردیف عمومی فرمول یکسان با export منبع داد. در خروجی، LevelDB قادر به بازکردن پوشهٔ Documents کاربر پردازش نبود. formalize بدون خواندن project database فرمول تحویل داد. اجرای realizability به پایگاه پروژه و موتورهایی مانند JKind یا Kind 2 وابسته است و هدف متفاوتی دارد. [نصب](https://github.com/NASA-SW-VnV/fret/blob/v3.1.0/fret-electron/docs/_media/installingFRET/installationInstructions.md) · [راهنمای CLI](https://github.com/NASA-SW-VnV/fret/blob/v3.1.0/fret-electron/docs/_media/cli/cli.md)

آزمون مستقل `python scripts/check_fret_projection.py` معنای دو export را روی ردهای سه‌گامی با مدل زمان محلی مقایسه می‌کند. تفاوت trigger در CSV و [راهنمای داده](DATASET_GUIDE.md) ثبت است. این مقایسه دلیل تجربی نیاز به یکسان‌سازی معنا پیش از آزمون زمان فراهم می‌کند.

## نتیجهٔ Hanfor و Ultimate

وابستگی‌های Python 3.12 در محیط جدا نصب شدند. پس از نصب Z3، CLI پاسخ داد. adapter از countertrace و Phase Event Automaton خود Hanfor و simulator آن استفاده کرد. روی جفت عمومی با سیگنال‌های مستقل، هر دو ابزار یک رد سازگار یافتند. روی نمونهٔ مشتق‌شدهٔ متناقض که همان سیگنال را هم الزام و هم منع می‌کند، Hanfor در بررسی گام مسدود شد و Z3 محلی UNSAT داد. این دو شاهد در `results/validation/hanfor_shared_subset.csv` ثبت شده‌اند. زمان simulator در مطالعهٔ اصلی وارد نشد. برای دو invariant تک‌بیتی سراسری، نمونهٔ ثابت کافی است. کامل بودن انتخاب نخستین گذار به ویژگی این دو نمونهٔ سراسری محدود است.

```bash
git clone --depth 1 --branch v1.2.1 https://github.com/ultimate-pa/hanfor.git /tmp/team3-hanfor
python3 -m venv /tmp/team3-hanfor-venv
/tmp/team3-hanfor-venv/bin/pip install -r /tmp/team3-hanfor/hanfor/requirements.txt z3-solver==4.15.4.0
PYTHONPATH=/tmp/team3-hanfor/hanfor /tmp/team3-hanfor-venv/bin/python scripts/check_hanfor_subset.py
```

دریافت ZIP مستندشدهٔ UReqCheck از شبانهٔ دانشگاه HTTP 403 داد و مسیر فایل آزموده‌شده روی release Ultimate v0.3.2، HTTP 404. مسیر مستند build به Java 11 و Maven نیاز دارد. در محیط اجرا Java 21 بود و Maven در PATH نبود. مقایسهٔ زمان end-to-end ابزار خارجی روی ورودی و هدف هم‌معنا هنوز باز است. در این گزارش روش‌های داخلی هم‌معنا و چک Hanfor شواهد جایگزین هستند و تأیید کفایت آن‌ها بر عهدهٔ استاد است. [راهنمای نصب Hanfor و ReqAnalyzer](https://ultimate-pa.github.io/hanfor/installation/installation.html) · [Ultimate v0.3.2](https://github.com/ultimate-pa/ultimate/releases/tag/v0.3.2)
