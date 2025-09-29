# 🌟 Telegram Star Collector Bot

A powerful automated Telegram bot that helps users earn stars by automatically joining channels and completing tasks. The bot features intelligent task detection, automatic channel joining, and comprehensive Arabic notifications.

## ✨ Features

- **🤖 Automated Task Completion**: Automatically joins channels and completes tasks
- **🎯 Smart Skip Detection**: Intelligently skips tutorial and instruction messages
- **🔗 Multi-URL Support**: Handles regular channels, private channels, and addlist URLs
- **⚡ Auto-Skip Failed Tasks**: Automatically skips tasks when channel joining fails
- **🌍 Arabic Notifications**: Comprehensive Arabic notifications for user-friendly experience
- **📊 Task Statistics**: Tracks completed tasks and earned rewards
- **🛡️ Error Handling**: Robust error handling for various scenarios
- **💾 Database Integration**: SQLite database for persistent user data

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/telegram-star-collector-bot.git
   cd telegram-star-collector-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configuration file:**
   
   Create a `config.py` file with your credentials:
   ```python
   # Telegram Bot Configuration
   BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
   
   # Telegram API Configuration
   API_ID = 12345  # Your API ID from my.telegram.org
   API_HASH = "your_api_hash_here"  # Your API Hash
   
   # Target Bot (the bot that gives star tasks)
   TARGET_BOT = "@StarsovGamesBot"  
   
   # Database Configuration
   DATABASE_FILE = "bot_database.db"
   
   # Bot Messages (Arabic)
   WELCOME_MESSAGE = """
   🌟 مرحباً بك في بوت تجميع النجوم التلقائي!
   
   هذا البوت يساعدك على:
   ⭐ تجميع النجوم تلقائياً
   🔗 الانضمام للقنوات المطلوبة
   📊 تتبع إحصائياتك
   
   للبدء، يرجى تسجيل حسابك أولاً.
   """
   
   REGISTER_ACCOUNT = "📱 تسجيل الحساب"
   START_COLLECTING = "🚀 بدء التجميع التلقائي"
   STOP_COLLECTING = "⏹️ إيقاف التجميع"
   ACCOUNT_STATUS = "📊 حالة الحساب"
   
   PHONE_REQUEST = "📱 يرجى إرسال رقم هاتفك مع رمز الدولة:\nمثال: +201234567890"
   CODE_REQUEST = "📱 تم إرسال رمز التحقق إلى هاتفك.\nيرجى إرسال الرمز:"
   TWO_FA_REQUEST = "🔐 يرجى إرسال كلمة مرور التحقق بخطوتين:"
   REGISTRATION_SUCCESS = "✅ تم تسجيل حسابك بنجاح!\nيمكنك الآن بدء التجميع التلقائي."
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## 🎮 Usage

### Getting Started

1. **Start the bot** by sending `/start`
2. **Register your account** using the "📱 تسجيل الحساب" button
3. **Provide your phone number** with country code
4. **Enter the verification code** sent to your phone
5. **Enter 2FA password** if enabled on your account
6. **Start collecting** using "🚀 بدء التجميع التلقائي"

### Bot Commands

- `/start` - Start the bot and show main menu
- Use keyboard buttons for navigation:
  - 📱 **تسجيل الحساب** - Register your Telegram account
  - 🚀 **بدء التجميع التلقائي** - Start automated star collection
  - ⏹️ **إيقاف التجميع** - Stop collection
  - 📊 **حالة الحساب** - View account statistics

## 🔧 Configuration

### Supported Target Bots

The bot is designed to work with star-earning bots like:
- @StarsovGamesBot
- Other similar bots if there was (configure in `TARGET_BOT`)

### Channel Types Supported

- **Public Channels**: `@channelname` or `https://t.me/channelname`
- **Private Channels**: `https://t.me/+invitehash`
- **Addlist URLs**: `https://t.me/addlist/hash`
- **Bot Links**: `https://t.me/botname`

## 📁 Project Structure

```
telegram-star-collector-bot/
├── bot.py                 # Main bot application
├── task_handler.py        # Task processing and channel joining logic
├── auth_handler.py        # Telegram authentication handling
├── database.py            # Database operations
├── config.py             # Configuration file (create this)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── LICENSE               # MIT License
└── .gitignore           # Git ignore file
```

## 🛠️ Key Components

### Task Handler (`task_handler.py`)
- Monitors target bot messages
- Processes channel joining tasks
- Handles different URL types
- Implements auto-skip functionality
- Manages task confirmations

### Authentication Handler (`auth_handler.py`)
- Manages Telegram user authentication
- Handles phone verification
- Manages 2FA authentication
- Creates and manages user sessions

### Database (`database.py`)
- SQLite database for user data
- Tracks completed tasks and rewards
- Stores user statistics
- Manages user settings

## 🔍 Features Breakdown

### Smart Message Detection
- Detects task messages vs tutorial messages
- Automatically skips instruction messages
- Prioritizes skip actions over submit actions

### Advanced Channel Joining
- Supports multiple URL formats
- Handles private channels and groups
- Processes addlist invitations
- Automatic error handling and retry logic

### Arabic User Interface
- Complete Arabic interface
- Comprehensive task completion notifications
- User-friendly error messages
- Progress tracking in Arabic

### Error Handling
- Graceful handling of join failures
- Automatic skip on invalid channels
- Flood control management
- Session management

## 📊 Statistics Tracked

- Total stars earned
- Number of completed tasks
- Daily task completion
- Success rate
- Account registration date
- Last activity time

## 🚨 Important Notes

### Security
- Never share your `config.py` file
- Keep your bot token and API credentials secure
- The bot creates local session files - keep them private

### Compliance
- Respect Telegram's Terms of Service
- Don't spam or abuse the service
- Use reasonable delays between actions
- Monitor your account for any issues

### Limitations
- Requires active internet connection
- Dependent on target bot availability
- Subject to Telegram API rate limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This bot is for educational purposes only. Users are responsible for complying with Telegram's Terms of Service and any applicable laws. The developers are not responsible for any misuse of this software.

## 📧 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/telegram-star-collector-bot/issues) section
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your setup and the issue

## 🌟 Star the Project

If you find this project helpful, please consider giving it a star ⭐ on GitHub!

---

**Happy Star Collecting! 🌟**