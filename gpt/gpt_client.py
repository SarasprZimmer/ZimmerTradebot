# gpt/gpt_client.py

import openai
import os
import base64
from gpt.prompt import build_analysis_prompt

openai.api_key = os.getenv("OPENAI_API_KEY")


def validate_chart_image(image_path):
    with open(image_path, "rb") as img:
        image_data = base64.b64encode(img.read()).decode("utf-8")

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """آیا تصویر زیر یک نمودار کندل استیک است که حدود ۳ تا ۴ روز را پوشش می‌دهد و قیمت‌ها و خطوط جداکننده در آن واضح هستند؟
لطفاً بررسی کن که کندل‌ها مشخص باشند، قیمت‌ها قابل خواندن باشند، و حدود ۳ یا ۴ روز را نمایش دهد — اما نیازی به تطبیق تاریخ با امروز نیست.
اگر تصویر معتبر است، فقط بنویس: valid.
اگر نه، دلیل را بنویس."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        max_tokens=100,
    )

    result = response.choices[0].message.content.strip().lower()
    if "valid" in result:
        return {"valid": True}
    else:
        return {"valid": False, "reason": result}


def run_analysis(image_path, price_data, pair_name=""):
    with open(image_path, "rb") as img:
        image_data = base64.b64encode(img.read()).decode("utf-8")

    prompt = build_analysis_prompt(pair_name, price_data["high"], price_data["low"], price_data["close"])

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content.strip()
def run_analysis_from_images(image_paths):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    image_contents = []
    for path in image_paths:
        with open(path, "rb") as img:
            image_base64 = base64.b64encode(img.read()).decode("utf-8")
            image_contents.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })

    prompt = """
امروز نقش شما یک تحلیل‌گر تکنیکال حرفه‌ای بازارهای مالی است.

تصویر اول شامل نمودار کندل استیک است.
تصویر دوم جدول قیمت‌هاست. لطفاً از آن جدول مقادیر High، Low و Close مربوط به ۴ روز گذشته را استخراج کن.
اگر جدول واضح نبود یا خوانا نیست، لطفاً اعلام کن که نیاز به ورود دستی داده‌هاست.

سپس تحلیل را بر اساس نقاط Pivot، R1، S1 انجام بده.
اعداد را رند کن. ساختار تحلیل باید شامل:

- مرور داده‌های استخراج‌شده
- بررسی هر روز به‌صورت خلاصه
- سناریوی صعودی
- سناریوی نزولی
- نتیجه‌گیری نهایی

زمان تحلیل باید مطابق با ساعت تهران (UTC+3:30) باشد.
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}] + image_contents
            }
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content.strip()

