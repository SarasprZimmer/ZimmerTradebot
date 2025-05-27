import os
import tempfile
import re
import base64
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.user_log import log_user, is_returning_user, log_feedback, increment_usage_count
from gpt.gpt_client import validate_chart_image, run_analysis, run_analysis_from_images
from gpt.prompt import build_analysis_prompt

WELCOME_NEW = "به ربات تحلیل‌گر خوش اومدی 👋\nبرای شروع یکی از گزینه‌ها رو انتخاب کن:"
WELCOME_BACK = "سلام! چه کاری می‌خوای انجام بدی؟👇"

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "NoUsername"
    first_time = not is_returning_user(chat_id)

    log_user(chat_id, username)
    context.user_data.clear()
    context.user_data["menu_shown"] = True

    keyboard = ReplyKeyboardMarkup(
        [["🟢 تحلیل نمودار", "💬 ثبت بازخورد"],
         ["📊 نمونه تحلیل", "❓ راهنما"]],
        resize_keyboard=True
    )

    welcome = WELCOME_NEW if first_time else WELCOME_BACK
    await context.bot.send_message(chat_id=chat_id, text=welcome, reply_markup=keyboard)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        await file.download_to_drive(temp_file.name)
        image_path = temp_file.name

    if not context.user_data.get("awaiting_chart"):
        await update.message.reply_text("❗ لطفاً ابتدا گزینه 'تحلیل نمودار' را انتخاب کن.")
        return

    if not context.user_data.get("chart_ok"):
        await update.message.reply_text("📸 در حال بررسی تصویر نمودار...")

        result = validate_chart_image(image_path)

        if result["valid"]:
            context.user_data["chart_ok"] = True
            context.user_data["chart_path"] = image_path
            await update.message.reply_text(
                "✅ نمودار معتبر است.\nحالا لطفاً مقادیر High, Low, Close را وارد کن — یا تصویر جدول را بفرست."
            )
        else:
            os.remove(image_path)
            await update.message.reply_text(f"❌ تصویر معتبر نیست. مشکل:\n{result['reason']}\nلطفاً تصویر بهتری ارسال کن.")
        return

    if "table_path" not in context.user_data:
        context.user_data["table_path"] = image_path
        await update.message.reply_text("📊 تصویر جدول دریافت شد. در حال تحلیل...")
        await process_dual_image_analysis(update, context)
    else:
        await update.message.reply_text("🚫 بیش از دو تصویر ارسال شده. فقط نمودار و جدول لازم است.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "NoUsername"
    text = update.message.text.strip()

    if not context.user_data.get("awaiting_chart") and not context.user_data.get("awaiting_feedback"):
        if text not in ["🟢 تحلیل نمودار", "💬 ثبت بازخورد", "📊 نمونه تحلیل", "❓ راهنما"]:
            await update.message.reply_text("❗ لطفاً ابتدا یکی از گزینه‌های منو را انتخاب کن.")
            return

    if text == "🟢 تحلیل نمودار":
        context.user_data.clear()
        context.user_data["awaiting_chart"] = True
        await update.message.reply_text("✅ حالت تحلیل فعال شد.\nلطفاً تصویر نمودار کندل استیک را ارسال کن.")
        return

    if text == "💬 ثبت بازخورد":
        context.user_data.clear()
        context.user_data["awaiting_feedback"] = True
        await update.message.reply_text("📝 لطفاً بازخورد خود را به صورت پیام ارسال کن.")
        return

    if text == "📊 نمونه تحلیل":
        await update.message.reply_text("📋 نمونه تحلیل:\n(برای مثال)\nسناریو صعودی: اگر قیمت بالای ۳۳۰۰ بماند...\nسناریو نزولی: در صورت افت زیر ۳۲۵۰...")
        return

    if text == "❓ راهنما":
        await update.message.reply_text("""
📘 راهنمای استفاده از ربات تحلیل‌گر:

این ربات بهت کمک می‌کنه تا با استفاده از هوش مصنوعی، نمودارهای کندل‌استیکت رو تحلیل کنی.

1️⃣ دکمه "🟢 تحلیل نمودار" رو بزن.
2️⃣ یک عکس واضح از نمودار کندل‌استیک خودت ارسال کن.
   ➤ عکس باید شامل حداقل ۳ و حداکثر ۴ روز باشه.
   ➤ خطوط جداکننده‌ی روزها و قیمت‌ها باید قابل دیدن باشه.
3️⃣ بعد از تایید تصویر، یکی از این دو کار رو انجام بده:
   - 🔢 مقادیر High, Low, Close رو به صورت متنی وارد کن
   - 🖼 یا یک عکس از جدول قیمت‌ها بفرست
4️⃣  ربات تحلیل تکنیکال کامل رو بهت می‌ده و میتونی سوالاتت رو هم ازش بپرسی! 📊

🔎 در ادامه، دو مثال از عکس درست و اشتباه رو ببین 👇
        """)

        with open("static/good_chart.jpg", "rb") as good:
            await update.message.reply_photo(
                photo=good,
                caption="✅ مثال درست: نمودار شامل ۴ روز با خطوط و اعداد واضح"
            )

        with open("static/bad_chart.jpg", "rb") as bad:
            await update.message.reply_photo(
                photo=bad,
                caption="❌ مثال اشتباه: اطلاعات قیمت مشخص نیست یا بزرگنمایی زیاد است"
            )
        return

    if context.user_data.get("awaiting_feedback"):
        log_feedback(chat_id, username, text)
        context.user_data.pop("awaiting_feedback")
        await update.message.reply_text("✅ بازخوردت ثبت شد. ممنونم! 🙏")
        return

    if "thread" in context.user_data and not re.search(r"(High|Low|Close)", text, re.IGNORECASE):
        thread = context.user_data["thread"]
        thread.append({"role": "user", "content": text})

        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=thread,
                max_tokens=700
            )
            answer = response.choices[0].message.content.strip()
            thread.append({"role": "assistant", "content": answer})
            await update.message.reply_text(answer)

        except Exception as e:
            print("❌ Error in follow-up Q&A:", e)
            await update.message.reply_text("⚠️ مشکلی پیش آمد در پاسخ به سوال. لطفاً دوباره تلاش کن.")
        return

    if not context.user_data.get("chart_ok"):
        await update.message.reply_text("❌ لطفاً ابتدا تصویر نمودار را ارسال کن.")
        return

    match = re.findall(r"(High|Low|Close)\s*:\s*([\d\s,\.]+)", text, re.IGNORECASE)
    if len(match) < 3:
        await update.message.reply_text(
            "❌ لطفاً داده‌ها را به یکی از روش‌های زیر وارد کن:\n\n1. وارد کردن دستی:\nHigh: ...\nLow: ...\nClose: ...\n2. ارسال تصویر جدول"
        )
        return

    price_data = {}
    for key, values in match:
        numbers = re.findall(r"\d+(?:\.\d+)?", values)
        if len(numbers) != 4:
            await update.message.reply_text(f"❌ فیلد {key} باید دقیقاً شامل ۴ عدد باشد.")
            return
        price_data[key.lower()] = list(map(float, numbers))

    await update.message.reply_text("🔍 در حال انجام تحلیل...")

    try:
        image_path = context.user_data.get("chart_path")
        analysis = run_analysis(image_path, price_data, pair_name="")

        await update.message.reply_text("📊 تحلیل نهایی:")
        await update.message.reply_text(analysis)

        increment_usage_count(chat_id, username)

        with open(image_path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode("utf-8")

        context.user_data["thread"] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_analysis_prompt("XAU/USD", price_data["high"], price_data["low"], price_data["close"])},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                ]
            },
            {"role": "assistant", "content": analysis}
        ]

    except Exception as e:
        print("❌ Error during GPT analysis:", e)
        await update.message.reply_text("⚠️ مشکلی در تحلیل پیش آمد. لطفاً دوباره تلاش کن.")

async def process_dual_image_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        image_paths = [
            context.user_data.get("chart_path"),
            context.user_data.get("table_path")
        ]
        analysis = run_analysis_from_images(image_paths)

        await update.message.reply_text("📊 تحلیل نهایی:")
        await update.message.reply_text(analysis)

        chat_id = update.effective_chat.id
        username = update.effective_user.username or "NoUsername"
        increment_usage_count(chat_id, username)

        context.user_data["thread"] = [{"role": "user", "content": [{"type": "text", "text": "تحلیل بر اساس نمودار و جدول"}]}]
        for path in image_paths:
            with open(path, "rb") as img:
                encoded = base64.b64encode(img.read()).decode("utf-8")
                context.user_data["thread"].append({
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}]
                })

        context.user_data["thread"].append({"role": "assistant", "content": analysis})

    except Exception as e:
        print("❌ Error in dual image analysis:", e)
        await update.message.reply_text("⚠️ مشکلی در تحلیل تصویر جدول پیش آمد. لطفاً دوباره تلاش کن.")
