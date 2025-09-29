import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError
from telethon.sessions import StringSession
from typing import Optional, Tuple, Dict, Any
import re

logger = logging.getLogger(__name__)

class AuthHandler:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.pending_auths: Dict[int, Dict[str, Any]] = {}
    
    def validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    async def start_auth(self, user_id: int, phone_number: str) -> Tuple[bool, str]:
        """Start the authentication process for a user"""
        try:
            if not self.validate_phone_number(phone_number):
                return False, "❌ رقم الهاتف غير صحيح. يرجى التأكد من التنسيق: +1234567890"
            
            # Create a new client for this authentication
            client = TelegramClient(StringSession(), self.api_id, self.api_hash)
            
            await client.connect()
            
            # Send code request
            sent_code = await client.send_code_request(phone_number)
            
            # Store the client and code info for this user
            self.pending_auths[user_id] = {
                'client': client,
                'phone': phone_number,
                'phone_code_hash': sent_code.phone_code_hash,
                'state': 'awaiting_code'
            }
            
            logger.info(f"Code sent to user {user_id} at {phone_number}")
            return True, "✅ تم إرسال رمز التحقق إلى رقمك. يرجى إرسال الرمز."
            
        except PhoneNumberInvalidError:
            return False, "❌ رقم الهاتف غير صالح."
        except Exception as e:
            logger.error(f"Error starting auth for user {user_id}: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"
    
    async def verify_code(self, user_id: int, code: str) -> Tuple[bool, str, Optional[str]]:
        """Verify the SMS code"""
        try:
            if user_id not in self.pending_auths:
                return False, "❌ لم يتم العثور على طلب تحقق نشط. يرجى البدء من جديد.", None
            
            auth_data = self.pending_auths[user_id]
            client = auth_data['client']
            phone = auth_data['phone']
            phone_code_hash = auth_data['phone_code_hash']
            
            try:
                # Try to sign in with the code
                user = await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=phone_code_hash
                )
                
                # Success - get session string
                session_string = client.session.save()
                await client.disconnect()
                
                # Clean up
                del self.pending_auths[user_id]
                
                logger.info(f"User {user_id} authenticated successfully")
                return True, "✅ تم تسجيل الدخول بنجاح!", session_string
                
            except SessionPasswordNeededError:
                # 2FA is enabled
                auth_data['state'] = 'awaiting_2fa'
                logger.info(f"User {user_id} needs 2FA")
                return True, "🔒 يرجى إرسال كلمة مرور التحقق الثنائي.", None
                
        except PhoneCodeInvalidError:
            return False, "❌ رمز التحقق غير صحيح. يرجى المحاولة مرة أخرى.", None
        except Exception as e:
            logger.error(f"Error verifying code for user {user_id}: {e}")
            return False, f"❌ حدث خطأ: {str(e)}", None
    
    async def verify_2fa(self, user_id: int, password: str) -> Tuple[bool, str, Optional[str]]:
        """Verify 2FA password"""
        try:
            if user_id not in self.pending_auths:
                return False, "❌ لم يتم العثور على طلب تحقق نشط. يرجى البدء من جديد.", None
            
            auth_data = self.pending_auths[user_id]
            if auth_data['state'] != 'awaiting_2fa':
                return False, "❌ لم يتم طلب التحقق الثنائي.", None
            
            client = auth_data['client']
            
            try:
                # Complete 2FA authentication
                user = await client.sign_in(password=password)
                
                # Success - get session string
                session_string = client.session.save()
                await client.disconnect()
                
                # Clean up
                del self.pending_auths[user_id]
                
                logger.info(f"User {user_id} completed 2FA authentication")
                return True, "✅ تم تسجيل الدخول بنجاح!", session_string
                
            except Exception as auth_error:
                logger.error(f"2FA auth error for user {user_id}: {auth_error}")
                return False, "❌ كلمة مرور التحقق الثنائي غير صحيحة.", None
                
        except Exception as e:
            logger.error(f"Error in 2FA verification for user {user_id}: {e}")
            return False, f"❌ حدث خطأ: {str(e)}", None
    
    async def cancel_auth(self, user_id: int) -> bool:
        """Cancel pending authentication for a user"""
        try:
            if user_id in self.pending_auths:
                auth_data = self.pending_auths[user_id]
                client = auth_data.get('client')
                if client and client.is_connected():
                    await client.disconnect()
                del self.pending_auths[user_id]
                logger.info(f"Cancelled authentication for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error cancelling auth for user {user_id}: {e}")
        return False
    
    def get_auth_state(self, user_id: int) -> Optional[str]:
        """Get the current authentication state for a user"""
        auth_data = self.pending_auths.get(user_id)
        return auth_data.get('state') if auth_data else None
    
    async def cleanup_expired_auths(self):
        """Clean up expired authentication attempts"""
        try:
            expired_users = []
            for user_id, auth_data in self.pending_auths.items():
                # You could add timestamp checking here
                # For now, we'll just clean up disconnected clients
                client = auth_data.get('client')
                if client and not client.is_connected():
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                await self.cancel_auth(user_id)
                
        except Exception as e:
            logger.error(f"Error cleaning up expired auths: {e}")

class TelegramUserClient:
    """Wrapper for user's Telegram client"""
    
    def __init__(self, api_id: int, api_hash: str, session_string: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.client = None
    
    async def connect(self) -> bool:
        """Connect the client"""
        try:
            self.client = TelegramClient(
                StringSession(self.session_string),
                self.api_id,
                self.api_hash
            )
            await self.client.start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect client: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect the client"""
        try:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting client: {e}")
    
    async def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.client and self.client.is_connected()
    
    async def get_me(self):
        """Get user information"""
        try:
            if self.client:
                return await self.client.get_me()
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
        return None