import os

BOT_TOKEN = ""  # Replace with your bot token from @BotFather

API_ID = 12626897  # Replace with your API ID
API_HASH = "169b4455fe17dddc8aebfa255a62a82d"  # Replace with your API hash

# Database configuration
DATABASE_FILE = "users.db"

# Target bot information
TARGET_BOT = "@StarsovGamesBot"
TARGET_BOT_USERNAME = "StarsovGamesBot"

# Retry configuration
MAX_RETRIES = 5
RETRY_DELAY = 300  # 5 minutes in seconds
TASK_CHECK_DELAY = 60  # 1 minute between task checks

# Messages
WELCOME_MESSAGE = """
🎯 مرحباً بك في بوت تجميع النجوم التلقائي!

هذا البوت سيساعدك في تجميع النجوم من @StarsovGamesBot تلقائياً.

لبدء الاستخدام، يرجى تسجيل حسابك أولاً:
"""

PHONE_REQUEST = """
📱 يرجى إرسال رقم هاتفك بالتنسيق التالي:
+1234567890

⚠️ تأكد من أن الرقم صحيح ومرتبط بحساب تيليجرام نشط.
"""

CODE_REQUEST = """
🔐 تم إرسال رمز التحقق إلى رقمك.
يرجى إرسال الرمز المكون من 5 أرقام.
"""

TWO_FA_REQUEST = """
🔒 يرجى إرسال كلمة مرور التحقق الثنائي الخاصة بك.
"""

REGISTRATION_SUCCESS = """
✅ تم تسجيل حسابك بنجاح!
يمكنك الآن بدء التجميع التلقائي.
"""

START_COLLECTING = "🚀 بدء التجميع التلقائي"
STOP_COLLECTING = "⏹️ إيقاف التجميع"
ACCOUNT_STATUS = "📊 حالة الحساب"
REGISTER_ACCOUNT = "📝 تسجيل حساب جديد"
