# ================================
# Telegram Star Collector Bot Configuration
# ================================
# 
# IMPORTANT: 
# 1. Copy this file to 'config.py'
# 2. Fill in your actual credentials
# 3. Never share your config.py file with anyone!

# ================================
# Telegram Bot Configuration
# ================================
# Get this from @BotFather on Telegram
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ================================
# Telegram API Configuration  
# ================================
# Get these from https://my.telegram.org
API_ID = 12345  # Replace with your API ID
API_HASH = "your_api_hash_here"  # Replace with your API Hash

# ================================
# Target Bot Configuration
# ================================
# The bot that provides star collection tasks
TARGET_BOT = "@StarsovGamesBot"  # Change this to your target bot

# ================================
# Database Configuration
# ================================
DATABASE_FILE = "bot_database.db"

# ================================
# Bot Messages (Arabic Interface)
# ================================

WELCOME_MESSAGE = """
🌟 مرحباً بك في بوت تجميع النجوم التلقائي!

هذا البوت يساعدك على:
⭐ تجميع النجوم تلقائياً
🔗 الانضمام للقنوات المطلوبة  
📊 تتبع إحصائياتك
🎯 تخطي المهام الفاشلة تلقائياً

للبدء، يرجى تسجيل حسابك أولاً.
"""

# Button Labels
REGISTER_ACCOUNT = "📱 تسجيل الحساب"
START_COLLECTING = "🚀 بدء التجميع التلقائي"
STOP_COLLECTING = "⏹️ إيقاف التجميع"
ACCOUNT_STATUS = "📊 حالة الحساب"

# Authentication Messages
PHONE_REQUEST = """
📱 يرجى إرسال رقم هاتفك مع رمز الدولة:

مثال: +201234567890
"""

CODE_REQUEST = """
📱 تم إرسال رمز التحقق إلى هاتفك.
يرجى إرسال الرمز:
"""

TWO_FA_REQUEST = """
🔐 يرجى إرسال كلمة مرور التحقق بخطوتين:
"""

REGISTRATION_SUCCESS = """
✅ تم تسجيل حسابك بنجاح!

يمكنك الآن بدء التجميع التلقائي للنجوم.
"""

# ================================
# Advanced Configuration
# ================================

# Delay settings (in seconds)
TASK_DELAY = 2  # Delay between tasks
CONFIRMATION_RETRY_DELAY = 3  # Delay between confirmation retries
SKIP_DELAY = 1  # Delay after skipping

# Retry settings
MAX_CONFIRMATION_RETRIES = 15  # Maximum confirmation attempts
MAX_SKIP_RETRIES = 3  # Maximum skip attempts

# Monitoring settings
PERIODIC_CHECK_INTERVAL = 300  # Check for new tasks every 5 minutes
NO_TASKS_WAIT_TIME = 120  # Wait time when no tasks available

# ================================
# Feature Flags
# ================================

# Enable/disable features
ENABLE_NOTIFICATIONS = True  # Send notifications to users
ENABLE_STATISTICS = True  # Track user statistics
ENABLE_AUTO_SKIP = True  # Auto-skip failed tasks
ENABLE_ARABIC_INTERFACE = True  # Use Arabic interface

# ================================
# Logging Configuration
# ================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ================================
# Security Settings
# ================================

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 20
FLOOD_WAIT_THRESHOLD = 60

# Session management
SESSION_TIMEOUT = 3600  # 1 hour in seconds
AUTO_DISCONNECT_INACTIVE = True