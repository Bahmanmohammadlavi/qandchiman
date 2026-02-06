import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode
import jdatetime

from db import db
from reports import report_generator

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
GLUCOSE, FASTING, TIME, SYMPTOMS = range(4)

# Bot token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ خطا: BOT_TOKEN در فایل .env تنظیم نشده است!")
    exit(1)

# ==================== KEYBOARD FUNCTIONS ====================


def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ ثبت آزمایش جدید", callback_data="new_test")],
        [
            InlineKeyboardButton(
                "📊 گزارش هفتگی", callback_data="weekly_report"),
            InlineKeyboardButton(
                "📈 گزارش ماهانه", callback_data="monthly_menu")
        ],
        [
            InlineKeyboardButton("📋 لیست آزمایش‌ها",
                                 callback_data="list_tests"),
            InlineKeyboardButton("📊 آمار کلی", callback_data="overall_stats")
        ],
        [InlineKeyboardButton("📖 راهنما", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_fasting_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🟦 ناشتا", callback_data="fasting_yes"),
            InlineKeyboardButton("🟧 غیرناشتا", callback_data="fasting_no")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_time_keyboard() -> InlineKeyboardMarkup:
    times = ["07:30", "08:00", "08:30", "09:00", "09:30",
             "10:00", "10:30", "11:00", "11:30", "12:00"]

    keyboard = []
    row = []
    for i, time_str in enumerate(times):
        row.append(InlineKeyboardButton(
            time_str, callback_data=f"time_{time_str}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel")]
    ])

    return InlineKeyboardMarkup(keyboard)


def get_symptoms_keyboard() -> InlineKeyboardMarkup:
    symptoms = [
        ("سرگیجه", "dizziness"),
        ("سردرد", "headache"),
        ("بیحالی", "lethargy"),
        ("گرفتگی عضلات", "muscle_cramp"),
        ("لرزش دست و پا", "tremor"),
        ("استفراغ", "vomiting"),
        ("تاری دید", "blurred_vision"),
        ("تشنگی بیش از حد", "thirst"),
        ("هیچکدام", "none")
    ]

    keyboard = []
    row = []
    for persian_name, callback_data in symptoms:
        row.append(InlineKeyboardButton(
            persian_name, callback_data=f"symptom_{callback_data}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel")]
    ])

    return InlineKeyboardMarkup(keyboard)


def get_months_keyboard() -> InlineKeyboardMarkup:
    current_year = jdatetime.datetime.now().year
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر",
        "مرداد", "شهریور", "مهر", "آبان",
        "آذر", "دی", "بهمن", "اسفند"
    ]

    keyboard = []
    row = []
    for i, month_name in enumerate(months, 1):
        row.append(InlineKeyboardButton(
            month_name, callback_data=f"month_{current_year}_{i}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(
        "🏠 منوی اصلی", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)


def get_report_types_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 نمودار", callback_data="chart"),
            InlineKeyboardButton("📋 اکسل", callback_data="excel")
        ],
        [
            InlineKeyboardButton("📝 متن", callback_data="text"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_months")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = f"""سلام {user.first_name} 👋

به ربات مدیریت قند خون خوش آمدید!

📌 **امکانات:**
• ثبت آزمایش‌های قند خون
• گزارش‌های هفتگی و ماهانه
• نمودارهای گرافیکی
• خروجی اکسل
• آمار و تحلیل

💡 **برای شروع:**
1. از دکمه‌های زیر استفاده کنید
2. یا «شروع» را تایپ کنید

برای راهنما «راهنما» را تایپ کنید."""

    await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """📖 **راهنمای ربات**

🔹 **ثبت آزمایش جدید:**
1. عدد قند خون را وارد کنید
2. وضعیت ناشتا بودن را انتخاب کنید
3. ساعت آزمایش را انتخاب کنید
4. علائم را انتخاب کنید

📊 **گزارش‌ها:**
• گزارش هفتگی: آمار ۷ روز گذشته
• گزارش ماهانه: آمار یک ماه خاص
• نمودار گرافیکی
• خروجی اکسل

📋 **مدیریت:**
• مشاهده لیست آزمایش‌ها
• مشاهده آمار کلی

برای شروع، «ثبت آزمایش جدید» را انتخاب کنید."""

    await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

# ==================== CONVERSATION HANDLERS ====================


async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "new_test":
        await query.edit_message_text(
            "🔹 **مرحله ۱ از ۴**\n\nلطفاً **عدد قند خون** خود را وارد کنید (مثلاً 120):",
            parse_mode=ParseMode.MARKDOWN
        )
        return GLUCOSE

    return ConversationHandler.END


async def get_glucose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        glucose = int(update.message.text.strip())

        if glucose <= 0 or glucose > 1000:
            await update.message.reply_text("❌ عدد نامعتبر! لطفاً عددی بین ۱ تا ۱۰۰۰ وارد کنید:")
            return GLUCOSE

        context.user_data['glucose'] = glucose

        await update.message.reply_text(
            "🔹 **مرحله ۲ از ۴**\n\nآیا آزمایش **ناشتا** بوده است؟",
            reply_markup=get_fasting_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return FASTING

    except ValueError:
        await update.message.reply_text("❌ لطفاً فقط عدد وارد کنید (مثلاً 120):")
        return GLUCOSE


async def get_fasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "fasting_yes":
        context.user_data['fasting'] = True
    elif query.data == "fasting_no":
        context.user_data['fasting'] = False
    elif query.data == "back":
        await query.edit_message_text(
            "🔹 **مرحله ۱ از ۴**\n\nلطفاً **عدد قند خون** خود را وارد کنید (مثلاً 120):",
            parse_mode=ParseMode.MARKDOWN
        )
        return GLUCOSE
    elif query.data == "cancel":
        await cancel_conversation(update, context)
        return ConversationHandler.END

    await query.edit_message_text(
        "🔹 **مرحله ۳ از ۴**\n\nلطفاً **ساعت آزمایش** را انتخاب کنید:",
        reply_markup=get_time_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    return TIME


async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("time_"):
        time_str = query.data[5:]  # Remove "time_" prefix
        context.user_data['time'] = time_str

        await query.edit_message_text(
            "🔹 **مرحله ۴ از ۴**\n\nلطفاً **علائم** خود را انتخاب کنید:",
            reply_markup=get_symptoms_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return SYMPTOMS

    elif query.data == "back":
        await query.edit_message_text(
            "🔹 **مرحله ۲ از ۴**\n\nآیا آزمایش **ناشتا** بوده است؟",
            reply_markup=get_fasting_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return FASTING

    elif query.data == "cancel":
        await cancel_conversation(update, context)
        return ConversationHandler.END

    return SYMPTOMS


async def get_symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("symptom_"):
        symptom_key = query.data[8:]  # Remove "symptom_" prefix

        symptom_map = {
            "dizziness": "سرگیجه",
            "headache": "سردرد",
            "lethargy": "بیحالی",
            "muscle_cramp": "گرفتگی عضلات",
            "tremor": "لرزش دست و پا",
            "vomiting": "استفراغ",
            "blurred_vision": "تاری دید",
            "thirst": "تشنگی بیش از حد",
            "none": "هیچکدام"
        }

        symptoms = symptom_map.get(symptom_key, symptom_key)

        try:
            # Save to database
            test_data = db.add_test(
                user_id=update.effective_user.id,
                glucose=context.user_data['glucose'],
                fasting=context.user_data['fasting'],
                test_time=context.user_data['time'],
                symptoms=symptoms,
                notes=""
            )

            if test_data:
                # Create success message
                fasting_text = "ناشتا 🟦" if context.user_data['fasting'] else "غیرناشتا 🟧"
                glucose = context.user_data['glucose']

                status = ""
                if context.user_data['fasting']:
                    if glucose < 70:
                        status = "⚠️ **هشدار:** قند خون پایین (هایپوگلیسمی)"
                    elif glucose <= 100:
                        status = "✅ **عالی:** در محدوده نرمال ناشتا"
                    elif glucose <= 125:
                        status = "⚠️ **هشدار:** پیش‌دیابتی"
                    else:
                        status = "🔴 **خطر:** دیابتی"
                else:
                    if glucose < 70:
                        status = "⚠️ **هشدار:** قند خون پایین (هایپوگلیسمی)"
                    elif glucose <= 140:
                        status = "✅ **عالی:** در محدوده نرمال"
                    elif glucose <= 200:
                        status = "⚠️ **هشدار:** بالا"
                    else:
                        status = "🔴 **خطر:** بسیار بالا"

                success_text = f"""✅ **آزمایش با موفقیت ثبت شد!**

📋 **جزئیات:**
• قند خون: {glucose} mg/dL
• نوع: {fasting_text}
• ساعت: {context.user_data['time']}
• علائم: {symptoms}
• تاریخ: {test_data['shamsi_date']}

📊 **تحلیل:**
{status}"""

                await query.edit_message_text(success_text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("❌ خطا در ذخیره‌سازی اطلاعات!", reply_markup=get_main_menu())

        except Exception as e:
            logger.error(f"Error saving test: {e}")
            await query.edit_message_text("❌ خطا در ثبت آزمایش!", reply_markup=get_main_menu())

        context.user_data.clear()
        return ConversationHandler.END

    elif query.data == "back":
        await query.edit_message_text(
            "🔹 **مرحله ۳ از ۴**\n\nلطفاً **ساعت آزمایش** را انتخاب کنید:",
            reply_markup=get_time_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return TIME

    elif query.data == "cancel":
        await cancel_conversation(update, context)
        return ConversationHandler.END

    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ عملیات لغو شد.", reply_markup=get_main_menu())
    else:
        await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=get_main_menu())

    context.user_data.clear()
    return ConversationHandler.END

# ==================== REPORT HANDLERS ====================


async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    stats = db.get_weekly_stats(user_id)

    if stats['count'] == 0:
        await query.edit_message_text("❌ هیچ آزمایشی در ۷ روز گذشته ثبت نشده است.", reply_markup=get_main_menu())
        return

    report = report_generator.create_text_report(stats['tests'], "هفتگی")
    await query.edit_message_text(report, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)


async def monthly_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    current_year = jdatetime.datetime.now().year
    await query.edit_message_text(
        f"📅 **گزارش ماهانه**\n\nلطفاً ماه مورد نظر را انتخاب کنید:\n\nسال: {current_year}",
        reply_markup=get_months_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )


async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("month_"):
        _, year_str, month_str = query.data.split("_")
        year = int(year_str)
        month = int(month_str)

        context.user_data['report_year'] = year
        context.user_data['report_month'] = month

        user_id = update.effective_user.id
        tests = db.get_monthly_tests(user_id, year, month)

        if not tests:
            months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
                      "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
            month_name = months[month - 1]
            await query.edit_message_text(f"❌ هیچ آزمایشی برای ماه {month_name} سال {year} یافت نشد.", reply_markup=get_main_menu())
            return

        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
                  "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        month_name = months[month - 1]

        await query.edit_message_text(
            f"📊 **گزارش ماه {month_name} سال {year}**\n\nتعداد آزمایش‌ها: {len(tests)}\n\nلطفاً نوع گزارش را انتخاب کنید:",
            reply_markup=get_report_types_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == "main_menu":
        await query.edit_message_text("به منوی اصلی برگشتید.", reply_markup=get_main_menu())


async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    year = context.user_data.get('report_year')
    month = context.user_data.get('report_month')

    if not year or not month:
        await query.edit_message_text("❌ خطا در دریافت اطلاعات ماه.", reply_markup=get_main_menu())
        return

    tests = db.get_monthly_tests(user_id, year, month)

    if not tests:
        await query.edit_message_text("❌ هیچ آزمایشی برای این ماه یافت نشد.", reply_markup=get_main_menu())
        return

    months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
              "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    month_name = months[month - 1]

    if query.data == "chart":
        chart_image = report_generator.create_monthly_chart(tests)

        if chart_image:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=chart_image,
                caption=f"📊 نمودار ماهانه قند خون - {month_name} {year}"
            )
            await query.edit_message_text(f"✅ نمودار ماه {month_name} ارسال شد.", reply_markup=get_main_menu())
        else:
            await query.edit_message_text("❌ خطا در ایجاد نمودار.", reply_markup=get_main_menu())

    elif query.data == "excel":
        excel_file = report_generator.create_excel_report(tests)

        if excel_file:
            await context.bot.send_document(
                chat_id=user_id,
                document=excel_file,
                filename=f"گزارش_قند_خون_{year}_{month}.xlsx",
                caption=f"📋 گزارش اکسل - {month_name} {year}"
            )
            await query.edit_message_text(f"✅ فایل اکسل ماه {month_name} ارسال شد.", reply_markup=get_main_menu())
        else:
            await query.edit_message_text("❌ خطا در ایجاد فایل اکسل.", reply_markup=get_main_menu())

    elif query.data == "text":
        text_report = report_generator.create_text_report(
            tests, f"ماهانه ({month_name})")

        if len(text_report) > 4000:
            parts = [text_report[i:i+4000]
                     for i in range(0, len(text_report), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await query.edit_message_text(part, parse_mode=ParseMode.MARKDOWN)
                else:
                    await context.bot.send_message(user_id, part, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(text_report, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

    elif query.data == "back_months":
        await monthly_menu(update, context)


async def list_tests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    tests = db.get_user_tests(user_id, limit=10)

    if not tests:
        await query.edit_message_text("❌ هیچ آزمایشی ثبت نشده است.", reply_markup=get_main_menu())
        return

    text = "📋 **آخرین آزمایش‌های شما**\n\n"

    for i, test in enumerate(tests, 1):
        fasting_emoji = "🟦" if test['fasting'] else "🟧"
        status_emoji = "🟢" if test['glucose'] <= 140 else "🟡" if test['glucose'] <= 200 else "🔴"

        text += f"{i}. {status_emoji} **{test['shamsi_date']}** - ساعت **{test['test_time']}**\n"
        text += f"   مقدار: **{test['glucose']}** mg/dL | نوع: {fasting_emoji} "
        text += "ناشتا\n" if test['fasting'] else "غیرناشتا\n"
        text += f"   علائم: {test['symptoms']}\n\n"

    text += f"\n📊 تعداد کل: {len(tests)}"

    await query.edit_message_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)


async def overall_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)

    if stats['total_tests'] == 0:
        await query.edit_message_text("❌ هیچ آزمایشی ثبت نشده است.", reply_markup=get_main_menu())
        return

    text = f"""📊 **آمار کلی شما**

• تعداد کل آزمایش‌ها: **{stats['total_tests']}**
• میانگین قند خون: **{stats['avg_glucose']:.1f}** mg/dL
• حداقل مقدار: **{stats['min_glucose']}** mg/dL
• حداکثر مقدار: **{stats['max_glucose']}** mg/dL"""

    if stats['last_test']:
        last = stats['last_test']
        glucose = last['glucose']

        text += "\n\n📈 **تحلیل آخرین آزمایش:**\n"
        if last['fasting']:
            if glucose < 70:
                text += "⚠️ **آخرین آزمایش:** قند خون پایین (هایپوگلیسمی)"
            elif glucose <= 100:
                text += "✅ **آخرین آزمایش:** در محدوده نرمال ناشتا"
            elif glucose <= 125:
                text += "⚠️ **آخرین آزمایش:** پیش‌دیابتی"
            else:
                text += "🔴 **آخرین آزمایش:** دیابتی"
        else:
            if glucose < 70:
                text += "⚠️ **آخرین آزمایش:** قند خون پایین (هایپوگلیسمی)"
            elif glucose <= 140:
                text += "✅ **آخرین آزمایش:** در محدوده نرمال"
            elif glucose <= 200:
                text += "⚠️ **آخرین آزمایش:** بالا"
            else:
                text += "🔴 **آخرین آزمایش:** بسیار بالا"

    await query.edit_message_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    text = """📖 **راهنمای ربات مدیریت قند خون**

🎯 **دستورات اصلی:**
• /start - شروع ربات
• راهنما - نمایش این راهنما

📋 **منوی اصلی:**
1. **ثبت آزمایش جدید** - ثبت آزمایش جدید قند خون
2. **گزارش هفتگی** - آمار ۷ روز گذشته
3. **گزارش ماهانه** - گزارش‌های یک ماه خاص
4. **لیست آزمایش‌ها** - مشاهده آخرین آزمایش‌ها
5. **آمار کلی** - آمار کلی کاربر

📊 **گزارش ماهانه شامل:**
• نمودار گرافیکی
• فایل اکسل برای چاپ
• گزارش متنی کامل

برای شروع، «ثبت آزمایش جدید» را انتخاب کنید."""

    await query.edit_message_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

# ==================== TEXT MESSAGE HANDLERS ====================


async def handle_start_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! برای ثبت آزمایش جدید لطفاً عدد قند خون خود را وارد کنید (مثلاً 120):",
        reply_markup=ReplyKeyboardRemove()
    )
    return GLUCOSE


async def handle_help_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)

# ==================== MAIN FUNCTION ====================


def main() -> None:
    print("🤖 ربات مدیریت قند خون در حال راه‌اندازی...")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_conversation, pattern='^new_test$'),
            MessageHandler(filters.TEXT & filters.Regex(
                r'^شروع$'), handle_start_text)
        ],
        states={
            GLUCOSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_glucose)
            ],
            FASTING: [
                CallbackQueryHandler(
                    get_fasting, pattern='^(fasting_yes|fasting_no|back|cancel)$')
            ],
            TIME: [
                CallbackQueryHandler(
                    get_time, pattern='^(time_.*|back|cancel)$')
            ],
            SYMPTOMS: [
                CallbackQueryHandler(
                    get_symptoms, pattern='^(symptom_.*|back|cancel)$')
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern='^cancel$'),
            CommandHandler('cancel', cancel_conversation)
        ],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(
        weekly_report, pattern='^weekly_report$'))
    application.add_handler(CallbackQueryHandler(
        monthly_menu, pattern='^monthly_menu$'))
    application.add_handler(CallbackQueryHandler(
        select_month, pattern='^month_'))
    application.add_handler(CallbackQueryHandler(
        generate_report, pattern='^(chart|excel|text|back_months)$'))
    application.add_handler(CallbackQueryHandler(
        list_tests, pattern='^list_tests$'))
    application.add_handler(CallbackQueryHandler(
        overall_stats, pattern='^overall_stats$'))
    application.add_handler(CallbackQueryHandler(show_help, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))

    # Add text message handlers
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^راهنما$'), handle_help_text))

    print("🔄 استفاده از polling...")
    print("✅ ربات آماده است! به تلگرام بروید و ربات را استارت کنید.")

    # Run bot
    application.run_polling()


if __name__ == '__main__':
    main()
