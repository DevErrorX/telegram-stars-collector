import asyncio
import logging
import re
from typing import Optional, Tuple, List, Dict, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message, KeyboardButtonCallback
from telethon.errors import FloodWaitError, ChannelPrivateError, UserAlreadyParticipantError, UserNotParticipantError, InviteHashExpiredError
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskHandler:
    def __init__(self, api_id: int, api_hash: str, target_bot: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.target_bot = target_bot
        self.running_tasks = {}

    async def start_collection(self, user_id: int, session_string: str) -> Tuple[bool, str]:
        try:
            if user_id in self.running_tasks:
                return False, "🔄 التجميع نشط بالفعل لهذا الحساب."
            
            from auth_handler import TelegramUserClient
            user_client = TelegramUserClient(self.api_id, self.api_hash, session_string)
            
            if not await user_client.connect():
                return False, "❌ فشل في الاتصال بحسابك. يرجى التحقق من صحة البيانات."
            
            self.running_tasks[user_id] = {
                'client': user_client,
                'active': True,
                'last_task_time': 0,
                'processing': False,
                'tasks_completed': 0,
                'start_time': datetime.now()
            }
            
            await self._setup_message_handler(user_id, user_client.client)
            asyncio.create_task(self._start_task_monitoring(user_id))
            asyncio.create_task(self._start_periodic_monitoring(user_id))
            
            logger.info(f"Started real-time collection for user {user_id}")
            return True, "🚀 تم بدء التجميع التلقائي!"
            
        except Exception as e:
            logger.error(f"Error starting collection for user {user_id}: {e}")
            await self._notify_user(user_id, f"❌ خطأ في بدء التجميع: {str(e)}")
            return False, f"❌ حدث خطأ: {str(e)}"

    async def stop_collection(self, user_id: int) -> Tuple[bool, str]:
        try:
            if user_id not in self.running_tasks:
                return False, "⏹️ لا يوجد تجميع نشط لإيقافه."
            
            task_data = self.running_tasks[user_id]
            task_data['active'] = False
            
            client = task_data.get('client')
            if client:
                await client.disconnect()
            
            del self.running_tasks[user_id]
            
            logger.info(f"Stopped collection for user {user_id}")
            return True, "⏹️ تم إيقاف التجميع التلقائي."
            
        except Exception as e:
            logger.error(f"Error stopping collection for user {user_id}: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    async def _process_task_message(self, user_id: int, message: Message, client: TelegramClient):
        try:
            message_text = message.text or ""
            
            channel_link = self._extract_channel_link(message_text)
            if not channel_link:
                await client.send_message(self.target_bot, "/start")
                return

            reward = self._extract_reward(message_text)
            join_result = await self._join_channel_fast(client, channel_link)
            
            if join_result == "pending":
                await self._handle_pending_channel(user_id, client)
                return
            elif not join_result:
                logger.info(f"Failed to join channel, attempting to skip for user {user_id}")
                # Try to skip the failed task automatically
                skip_success = await self._click_skip_button_fast(user_id, client)
                if skip_success:
                    logger.info(f"Successfully skipped failed task for user {user_id}")
                    await asyncio.sleep(1)
                    await client.send_message(self.target_bot, "/start")
                else:
                    # If skip fails, just restart
                    await asyncio.sleep(2)
                    await client.send_message(self.target_bot, "/start")
                return
            
            await asyncio.sleep(1.5)
            await self._handle_confirmation_with_retry(user_id, message, client)
            
        except Exception as e:
            logger.error(f"Error processing task message for user {user_id}: {e}")
            await self._notify_user(user_id, f"❌ خطأ في معالجة المهمة: {str(e)}")

    async def _handle_skip_message(self, user_id: int, message: Message, client: TelegramClient):
        try:
            success = await self._click_skip_button_fast(user_id, client)
            if success:
                await asyncio.sleep(1)
                await client.send_message(self.target_bot, "/start")
        except Exception as e:
            logger.error(f"Error handling skip for user {user_id}: {e}")

    async def _click_skip_button_fast(self, user_id: int, client: TelegramClient) -> bool:
        try:
            messages = await client.get_messages(self.target_bot, limit=5)
            
            # First, look for actual skip buttons
            for msg in messages:
                if hasattr(msg, 'reply_markup') and msg.reply_markup:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                button_text = button.text.lower()
                                skip_keywords = ['⏩', 'skip', 'пропустить', 'пропуск', 'далее', 'next']
                                if any(keyword in button_text for keyword in skip_keywords):
                                    from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
                                    await client(GetBotCallbackAnswerRequest(
                                        peer=self.target_bot,
                                        msg_id=msg.id,
                                        data=button.data
                                    ))
                                    logger.info(f"Clicked skip button: {button.text} for user {user_id}")
                                    return True
            
            # If no skip button found, try sending skip commands
            logger.info(f"No skip button found, sending skip commands for user {user_id}")
            await client.send_message(self.target_bot, "⏩")
            await asyncio.sleep(0.5)
            await client.send_message(self.target_bot, "Skip")
            await asyncio.sleep(0.5)
            await client.send_message(self.target_bot, "Пропустить")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking skip button for user {user_id}: {e}")
            return False

    async def _setup_message_handler(self, user_id: int, client: TelegramClient):
        @client.on(events.NewMessage(from_users=[self.target_bot]))
        async def handle_bot_message(event):
            try:
                task_data = self.running_tasks.get(user_id)
                if not task_data or not task_data.get('active'):
                    return
                
                if task_data.get('processing'):
                    return
                
                logger.info(f"New message from {self.target_bot} for user {user_id}: {event.message.text[:100]}...")
                asyncio.create_task(self._handle_new_message(user_id, event.message))
                
            except Exception as e:
                logger.error(f"Error in message handler for user {user_id}: {e}")

    async def _start_task_monitoring(self, user_id: int):
        try:
            await asyncio.sleep(2)
            
            task_data = self.running_tasks.get(user_id)
            if not task_data or not task_data.get('active'):
                return
            
            client = task_data['client'].client
            logger.info(f"Requesting initial task for user {user_id}")
            await client.send_message(self.target_bot, "/start")
            
        except Exception as e:
            logger.error(f"Error starting task monitoring for user {user_id}: {e}")

    async def _handle_new_message(self, user_id: int, message: Message):
        try:
            task_data = self.running_tasks.get(user_id)
            if not task_data or not task_data.get('active'):
                return
            
            task_data['processing'] = True
            client = task_data['client'].client
            message_text = message.text or ""
            
            logger.info(f"Processing message for user {user_id}: {message_text[:100]}")
            
            if "Вы делаете слишком много запросов" in message_text or "too many requests" in message_text.lower():
                await asyncio.sleep(5)
                await client.send_message(self.target_bot, "/start")
                return
            
            # Check for task completion messages with comprehensive detection
            if ("✅ Задание выполнено!" in message_text or 
                "Получено" in message_text or 
                "задание выполнено" in message_text.lower() or
                "Task completed" in message_text or
                "Completed" in message_text):
                
                if not task_data.get('confirming'):
                    reward = self._extract_reward(message_text)
                    
                    # Update task counter
                    task_data['tasks_completed'] = task_data.get('tasks_completed', 0) + 1
                    
                    # Create comprehensive Arabic notification
                    completion_message = self._create_task_completion_message(reward, task_data['tasks_completed'])
                    await self._notify_user(user_id, completion_message)
                    
                    # Save to database
                    from database import DatabaseManager
                    from config import DATABASE_FILE
                    db = DatabaseManager(DATABASE_FILE)
                    db.add_task(user_id, "channel_join", "", reward)
                    
                    logger.info(f"Task completed for user {user_id}: +{reward}⭐ (Total tasks: {task_data['tasks_completed']})")
                
                await asyncio.sleep(2)
                await client.send_message(self.target_bot, "/start")
                return
            
            if self._is_task_message(message_text):
                await self._process_task_message(user_id, message, client)
                return
                
            if "задания закончились" in message_text.lower() or "no tasks available" in message_text.lower():
                await asyncio.sleep(120)
                await client.send_message(self.target_bot, "/start")
                return
            
            # Check for skip messages FIRST, before confirmation messages
            if ("💡 Получайте** Звёзды** за **простые задания!** 👇" in message_text or 
                "💡 Получайте Звёзды за простые задания!" in message_text or 
                "1.** **Нажмите «Подписаться»**, дождитесь прогру" in message_text or
                "1. Нажмите «Подписаться», дождитесь прогрузки ссылки и подпишитесь" in message_text or
                "⏩" in message_text or "Skip" in message_text.lower() or "Пропустить" in message_text.lower() or
                "Нажмите «Подписаться», дождитесь прогрузки ссылки" in message_text):
                logger.info(f"Skip message detected for user {user_id}")
                await self._handle_skip_message(user_id, message, client)
                return
                
            if "Подтвердить" in message_text or "Confirm" in message_text or any(btn for btn in ["✅", "подтверд"] if btn in message_text.lower()):
                await self._handle_confirmation_with_retry(user_id, message, client)
                return
            
        except Exception as e:
            logger.error(f"Error handling message for user {user_id}: {e}")
        finally:
            if user_id in self.running_tasks:
                self.running_tasks[user_id]['processing'] = False

    async def _handle_confirmation_with_retry(self, user_id: int, message: Message, client: TelegramClient):
        try:
            task_data = self.running_tasks.get(user_id, {})
            task_data['confirming'] = True
            
            max_retries = 15
            retry_count = 0
            task_completed = False
            
            while retry_count < max_retries and not task_completed:
                retry_count += 1
                
                button_clicked = await self._click_confirmation_button_retry(user_id, client)
                await asyncio.sleep(3)
                
                recent_messages = await client.get_messages(self.target_bot, limit=3)
                for msg in recent_messages:
                    if msg.text and ("✅ Задание выполнено!" in msg.text or 
                                   "Получено" in msg.text or 
                                   "задание выполнено" in msg.text.lower() or
                                   "Task completed" in msg.text or
                                   "Completed" in msg.text):
                        task_completed = True
                        reward = self._extract_reward(msg.text)
                        
                        task_data = self.running_tasks.get(user_id, {})
                        task_data['tasks_completed'] = task_data.get('tasks_completed', 0) + 1
                        
                        # Create comprehensive Arabic notification
                        completion_message = self._create_task_completion_message(reward, task_data['tasks_completed'])
                        await self._notify_user(user_id, completion_message)
                        
                        from database import DatabaseManager
                        from config import DATABASE_FILE
                        db = DatabaseManager(DATABASE_FILE)
                        db.add_task(user_id, "channel_join", "", reward)
                        
                        logger.info(f"Task completed for user {user_id}: +{reward}⭐ (Total tasks: {task_data['tasks_completed']})")
                        
                        await asyncio.sleep(2)
                        await client.send_message(self.target_bot, "/start")
                        return
            
            if not task_completed:
                await self._notify_user(user_id, f"❌ فشل في الحصول على المكافأة")
                await asyncio.sleep(2)
                await client.send_message(self.target_bot, "/start")
            
        except Exception as e:
            logger.error(f"Error in confirmation retry for user {user_id}: {e}")
            await self._notify_user(user_id, "❌ خطأ في عملية التأكيد")
            await client.send_message(self.target_bot, "/start")
        finally:
            if user_id in self.running_tasks:
                self.running_tasks[user_id]['confirming'] = False

    async def _click_confirmation_button_retry(self, user_id: int, client: TelegramClient) -> bool:
        try:
            messages = await client.get_messages(self.target_bot, limit=3)
            
            for msg in messages:
                if hasattr(msg, 'reply_markup') and msg.reply_markup:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                button_text = button.text.lower()
                                confirmation_words = ['подтверд', '✅', 'confirm', 'check', 'подтвердить']
                                if any(word in button_text for word in confirmation_words):
                                    from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
                                    await client(GetBotCallbackAnswerRequest(
                                        peer=self.target_bot,
                                        msg_id=msg.id,
                                        data=button.data
                                    ))
                                    logger.info(f"Clicked confirmation button: {button.text}")
                                    return True
            
            await client.send_message(self.target_bot, "Подтвердить")
            await asyncio.sleep(0.5)
            await client.send_message(self.target_bot, "✅")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking confirmation button for user {user_id}: {e}")
            return False

    async def _start_periodic_monitoring(self, user_id: int):
        try:
            while True:
                task_data = self.running_tasks.get(user_id)
                if not task_data or not task_data.get('active'):
                    break
                
                await asyncio.sleep(300)
                
                if (task_data.get('active') and 
                    not task_data.get('processing') and 
                    not task_data.get('confirming')):
                    
                    client = task_data['client'].client
                    logger.info(f"Periodic check for user {user_id} - requesting new tasks")
                    await client.send_message(self.target_bot, "/start")
                
        except Exception as e:
            logger.error(f"Error in periodic monitoring for user {user_id}: {e}")

    def _is_task_message(self, text: str) -> bool:
        text_lower = text.lower()
        
        referral_indicators = [
            "приглашенного друга",
            "реферальная ссылка",
            "starsovgamesbot?start=",
            "приглашайте по этой ссылке",
            "приглашено вами:"
        ]
        
        if any(indicator in text_lower for indicator in referral_indicators):
            logger.info("Ignoring referral message")
            return False
        
        channel_task_indicators = [
            "подпишитесь на канал",
            "🔴 подпишитесь на канал",
            "🔴 subscribe to",
            "нажмите «подтвердить»"
        ]
        
        has_channel_task = any(indicator in text_lower for indicator in channel_task_indicators)
        has_valid_channel_link = bool(self._extract_channel_link(text))
        has_reward = "вознаграждение:" in text_lower
        
        logger.info(f"Task analysis: channel_task={has_channel_task}, valid_link={has_valid_channel_link}, reward={has_reward}")
        
        is_task = has_channel_task and has_valid_channel_link and has_reward
        if is_task:
            logger.info("✅ Valid channel task detected!")
        
        return is_task

    async def _join_channel_fast(self, client, channel_link: str):
        try:
            logger.info(f"Processing link: {channel_link}")
            
            # Handle different types of links
            if '/addlist/' in channel_link:
                # Handle addlist links (these are for multiple channels/groups)
                logger.info(f"Detected addlist link: {channel_link}")
                invite_hash = channel_link.split('/addlist/')[-1]
                from telethon.tl.functions.messages import ImportChatInviteRequest
                try:
                    await client(ImportChatInviteRequest(invite_hash))
                    logger.info(f"Joined via addlist: {invite_hash}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to join addlist {invite_hash}: {e}")
                    return False
            
            if self._is_bot_link(channel_link):
                channel_username = channel_link.split('/')[-1].split('?')[0]
                logger.info(f"Detected bot link: {channel_username}")
                return await self._start_bot(client, channel_username)
            
            # Extract channel username/hash
            if channel_link.startswith('https://t.me/+') or channel_link.startswith('t.me/+'):
                # Private channel with invite hash
                invite_hash = channel_link.split('+')[-1]
                from telethon.tl.functions.messages import ImportChatInviteRequest
                await client(ImportChatInviteRequest(invite_hash))
                logger.info(f"Joined private channel/group: {invite_hash}")
            else:
                # Public channel
                channel_username = channel_link.split('/')[-1]
                if channel_username.startswith('@'):
                    channel_username = channel_username[1:]
                
                from telethon.tl.functions.channels import JoinChannelRequest
                await client(JoinChannelRequest(channel_username))
                logger.info(f"Joined public channel/group: {channel_username}")
            
            return True
            
        except UserAlreadyParticipantError:
            logger.info(f"Already member of channel")
            return True
            
        except ChannelPrivateError:
            logger.warning(f"Channel is private or doesn't exist")
            return False
            
        except InviteHashExpiredError:
            logger.warning(f"Invite link expired")
            return False
            
        except Exception as e:
            error_msg = str(e).lower()
            if "successfully requested to join" in error_msg or "join request sent" in error_msg:
                logger.info(f"Join request sent (needs approval)")
                return "pending"
            elif "flood" in error_msg:
                logger.warning(f"Flood wait error")
                return False
            elif "nobody is using this username" in error_msg:
                logger.warning(f"Invalid username or channel doesn't exist")
                return False
            elif "unacceptable" in error_msg:
                logger.warning(f"Username format is unacceptable")
                return False
            else:
                logger.error(f"Failed to join channel: {e}")
                return False

    def _extract_channel_link(self, text: str) -> Optional[str]:
        try:
            patterns = [
                r'https://t\.me/\+[A-Za-z0-9\-_]+',  # Private channels
                r't\.me/\+[A-Za-z0-9\-_]+',
                r'https://t\.me/addlist/[A-Za-z0-9\-_]+',  # Addlist links
                r't\.me/addlist/[A-Za-z0-9\-_]+',
                r'https://t\.me/[A-Za-z0-9\-_]+',  # Regular channels
                r't\.me/[A-Za-z0-9\-_]+',
                r'@[A-Za-z0-9\-_]+'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    link = matches[0]
                    logger.info(f"Found channel link: {link}")
                    
                    if not link.startswith('http'):
                        if link.startswith('@'):
                            link = 'https://t.me/' + link[1:]
                        else:
                            link = 'https://' + link
                    
                    excluded_patterns = [
                        'StarsovGamesBot',
                        '?start=',
                        '/start',
                        'bot?start'
                    ]
                    
                    if not any(pattern in link for pattern in excluded_patterns):
                        logger.info(f"Valid channel link found: {link}")
                        return link
                    else:
                        logger.info(f"Excluded bot/referral link: {link}")
            
            return None
        except Exception as e:
            logger.error(f"Error extracting channel link: {e}")
            return None

    def _extract_reward(self, text: str) -> float:
        try:
            # Multiple patterns to catch different reward formats
            patterns = [
                r'\+([0-9]+\.?[0-9]*)\s*⭐',  # +0.25⭐
                r'Получено:\s*\+([0-9]+\.?[0-9]*)⭐',  # Получено: +0.25⭐
                r'([0-9]+\.?[0-9]*)\s*⭐',  # 0.25⭐
                r'reward:\s*([0-9]+\.?[0-9]*)',  # reward: 0.25
                r'([0-9]+\.?[0-9]*)\s*stars?'  # 0.25 star(s)
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    reward = float(matches[0])
                    logger.info(f"Extracted reward: {reward} from text: {text[:50]}...")
                    return reward
            
            logger.warning(f"No reward found in text, using default: {text[:50]}...")
            return 0.25
        except Exception as e:
            logger.error(f"Error extracting reward: {e}")
            return 0.25

    def _extract_channel_name(self, channel_link: str) -> str:
        try:
            if 't.me/' in channel_link:
                channel_part = channel_link.split('t.me/')[-1]
                if channel_part.startswith('+'):
                    return f"Private Channel ({channel_part[:15]}...)"
                else:
                    return f"@{channel_part}"
            return "Unknown Channel"
        except Exception as e:
            logger.error(f"Error extracting channel name: {e}")
            return "Unknown Channel"

    def _is_bot_link(self, link: str) -> bool:
        try:
            if 't.me/' in link:
                username = link.split('t.me/')[-1]
                if '?' in username:
                    username = username.split('?')[0]
                return username.lower().endswith('bot')
            return False
        except Exception as e:
            logger.error(f"Error checking if bot link: {e}")
            return False

    async def _start_bot(self, client, bot_username: str) -> bool:
        try:
            logger.info(f"Starting bot: {bot_username}")
            
            await client.send_message(bot_username, "/start")
            await asyncio.sleep(2)
            
            messages = await client.get_messages(bot_username, limit=3)
            
            for msg in messages:
                if hasattr(msg, 'reply_markup') and msg.reply_markup:
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                try:
                                    from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
                                    await client(GetBotCallbackAnswerRequest(
                                        peer=bot_username,
                                        msg_id=msg.id,
                                        data=button.data
                                    ))
                                    logger.info(f"Clicked bot button: {button.text}")
                                    return True
                                except Exception as e:
                                    logger.warning(f"Failed to click bot button: {e}")
                                    continue
            
            logger.info(f"Bot started successfully: {bot_username}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot {bot_username}: {e}")
            return False

    async def _handle_pending_channel(self, user_id: int, client: TelegramClient):
        try:
            await asyncio.sleep(2)
            
            success = await self._click_skip_button_fast(user_id, client)
            if success:
                await asyncio.sleep(2)
                await client.send_message(self.target_bot, "/start")
            else:
                await asyncio.sleep(2)
                await client.send_message(self.target_bot, "/start")
                
        except Exception as e:
            logger.error(f"Error handling pending channel for user {user_id}: {e}")

    def _create_task_completion_message(self, reward: float, total_tasks: int) -> str:
        """
        Create a comprehensive Arabic notification message for task completion
        """
        try:
            message = f"""
✅ **تم إنهاء مهمة بنجاح!**

⭐ **المكافأة:** +{reward} ⭐
📊 **إجمالي المهام:** {total_tasks}

⚠️ **تذكير مهم:** لا تقم بإلغاء اشتراكك في القناة لمدة 7 أيام على الأقل حتى تتجنب الغرامة أو الحظر.

🚀 **يتم البحث عن مهمة جديدة...**
            """.strip()
            
            return message
        except Exception as e:
            logger.error(f"Error creating completion message: {e}")
            return f"✅ تم إنهاء مهمة! +{reward}⭐"

    async def _notify_user(self, user_id: int, message: str):
        try:
            logger.info(f"Notification for user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")

    def get_running_tasks(self) -> List[int]:
        return list(self.running_tasks.keys())

    def is_user_collecting(self, user_id: int) -> bool:
        return user_id in self.running_tasks and self.running_tasks[user_id].get('active', False)