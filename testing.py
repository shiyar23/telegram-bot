import logging
import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة المتغيرات من البيئة
BOT_TOKEN = os.getenv('BOT_TOKEN')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# إعداد Google Sheets
def get_sheets_service():
    service_account_info = json.loads(os.getenv('SERVICE_ACCOUNT_JSON'))
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=credentials)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'مرحبا! أرسل البيانات التي تريد تسجيلها في Google Sheets.\n'
        'مثال: "2023-10-16, 100, Buy, USDJPY" (افصل بفواصل).'
    )

# معالج الرسائل
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        data = [item.strip() for item in text.split(',')]
        if len(data) < 1 or not data[0]:
            await update.message.reply_text('يرجى إرسال بيانات صالحة.')
            return

        sheets_service = get_sheets_service()
        values = [data]
        body = {'values': values}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A1',
            valueInputOption='RAW',
            body=body
        ).execute()

        await update.message.reply_text(
            f'تم التسجيل بنجاح!\n'
            f'البيانات: {text}\n'
            f'الجدول: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit'
        )
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        await update.message.reply_text(f'خطأ: {str(e)}')

# معالج الأخطاء
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    if not BOT_TOKEN:
        print("خطأ: BOT_TOKEN غير موجود")
        return
    if not SPREADSHEET_ID:
        print("خطأ: SPREADSHEET_ID غير موجود")
        return
    if not os.getenv('SERVICE_ACCOUNT_JSON'):
        print("خطأ: SERVICE_ACCOUNT_JSON غير موجود")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    print("البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == '__main__':
    main()