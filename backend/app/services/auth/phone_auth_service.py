"""Phone authentication service using WhatsApp OTP."""

from __future__ import annotations

import logging
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import jwt
from supabase import Client

from app.integrations.kapso import KapsoClient

logger = logging.getLogger(__name__)


class CodeExpiredError(Exception):
    """Verification code has expired."""

    pass


class CodeNotFoundError(Exception):
    """No verification code found for phone number."""

    pass


class InvalidCodeError(Exception):
    """Invalid verification code."""

    pass


class MaxAttemptsExceededError(Exception):
    """Maximum verification attempts exceeded."""

    pass


class PhoneAuthService:
    """Service for phone-based authentication using WhatsApp OTP."""

    def __init__(self, supabase: Client):
        """
        Initialize phone auth service.

        Args:
            supabase: Supabase client (with service role key for admin operations)
        """
        self.supabase = supabase

        # Create a non-admin client for creating user sessions
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        self.supabase_anon = Client(supabase_url, supabase_anon_key)

        # Initialize Kapso client for WhatsApp templates
        kapso_api_key = os.getenv("KAPSO_API_TOKEN")
        if not kapso_api_key:
            raise ValueError("KAPSO_API_TOKEN environment variable is required")
        self.kapso = KapsoClient(api_token=kapso_api_key)

        # Configuration
        self.code_expiry_minutes = int(os.getenv("PHONE_VERIFICATION_CODE_EXPIRY_MINUTES", "5"))
        self.max_attempts = int(os.getenv("PHONE_VERIFICATION_MAX_ATTEMPTS", "3"))
        self.cooldown_seconds = int(os.getenv("PHONE_VERIFICATION_COOLDOWN_SECONDS", "60"))

        # WhatsApp template configuration
        # Note: This template must be pre-approved by WhatsApp in the Kapso dashboard
        self.verification_template_name = os.getenv("PHONE_VERIFICATION_TEMPLATE_NAME", "authentication_code")
        self.verification_template_language = os.getenv("PHONE_VERIFICATION_TEMPLATE_LANGUAGE", "es")

    def _generate_code(self) -> str:
        """
        Generate a random 6-digit verification code.

        Returns:
            Six-digit numeric code as string
        """
        # Use secrets for cryptographically secure random numbers
        code = secrets.randbelow(1000000)
        return f"{code:06d}"

    def _generate_jwt_tokens(self, user_id: str, phone_number: str, email: Optional[str] = None) -> tuple[str, str]:
        """
        Generate JWT access and refresh tokens compatible with Supabase.

        Args:
            user_id: User's UUID
            phone_number: User's phone number
            email: User's email (optional)

        Returns:
            Tuple of (access_token, refresh_token)
        """
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET must be set in environment variables")

        now = int(time.time())
        access_token_exp = now + 3600  # 1 hour
        refresh_token_exp = now + (30 * 24 * 3600)  # 30 days
        session_id = str(uuid.uuid4())  # Must be a valid UUID

        # Access token payload (compatible with Supabase)
        access_payload = {
            "aud": "authenticated",
            "exp": access_token_exp,
            "iat": now,
            "iss": "supabase",
            "sub": user_id,
            "email": email or "",
            "phone": phone_number,
            "app_metadata": {
                "provider": "phone",
                "providers": ["phone"]
            },
            "user_metadata": {
                "verified_via": "whatsapp_otp"
            },
            "role": "authenticated",
            "aal": "aal1",
            "amr": [
                {
                    "method": "otp",
                    "timestamp": now
                }
            ],
            "session_id": session_id,
        }

        # Refresh token payload (longer expiry)
        refresh_payload = {
            "aud": "authenticated",
            "exp": refresh_token_exp,
            "iat": now,
            "iss": "supabase",
            "sub": user_id,
            "session_id": session_id,
        }

        access_token = jwt.encode(access_payload, jwt_secret, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, jwt_secret, algorithm="HS256")

        return (access_token, refresh_token)

    async def request_verification_code(
        self,
        phone_number: str,
    ) -> dict[str, Any]:
        """
        Generate and send verification code to phone number via WhatsApp.

        Args:
            phone_number: Phone number in E.164 format (e.g., +56912345678)

        Returns:
            Dict with success status, expiry time, and retry_after seconds

        Raises:
            ValueError: If rate limit exceeded or WhatsApp send fails
        """
        # Check for recent code requests (rate limiting)
        await self._check_rate_limit(phone_number)

        # Generate verification code
        code = self._generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)

        # Save code to database
        verification_record = self.supabase.table("phone_verification_codes").insert({
            "phone_number": phone_number,
            "code": code,
            "expires_at": expires_at.isoformat(),
            "attempts": 0,
            "max_attempts": self.max_attempts,
            "metadata": {
                "requested_at": datetime.utcnow().isoformat(),
            }
        }).execute()

        logger.info(f"Verification code generated for {phone_number}")

        # Send verification code via WhatsApp template
        try:
            # Get Phone Number ID from env
            phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            if not phone_number_id:
                raise ValueError("WHATSAPP_PHONE_NUMBER_ID environment variable is required")

            # Send template via Kapso Templates API with named parameters
            await self.kapso.templates.send_with_params(
                phone_number=phone_number,
                template_name=self.verification_template_name,
                phone_number_id=phone_number_id,
                template_params={"codigo": code},  # Named parameter
                template_language=self.verification_template_language,
            )

            logger.info(f"✅ Verification code sent to {phone_number} via WhatsApp template")

        except Exception as e:
            logger.error(f"Failed to send verification code via WhatsApp: {e}")
            # Delete the code from database if send fails
            self.supabase.table("phone_verification_codes").delete().eq(
                "id", verification_record.data[0]["id"]
            ).execute()
            raise ValueError(
                f"No se pudo enviar el código por WhatsApp. Error: {str(e)}"
            )

        return {
            "success": True,
            "expires_at": expires_at,
            "retry_after": self.cooldown_seconds,
        }

    async def verify_code(
        self,
        phone_number: str,
        code: str,
    ) -> dict[str, Any]:
        """
        Verify code and authenticate user.

        Args:
            phone_number: Phone number in E.164 format
            code: Six-digit verification code

        Returns:
            Dict with access_token, user info, etc.

        Raises:
            CodeNotFoundError: No code found for phone number
            CodeExpiredError: Code has expired
            InvalidCodeError: Code is incorrect
            MaxAttemptsExceededError: Too many failed attempts
        """
        # Find active verification code
        response = self.supabase.table("phone_verification_codes").select("*").eq(
            "phone_number", phone_number
        ).is_("verified_at", "null").order("created_at", desc=True).limit(1).execute()

        if not response.data:
            raise CodeNotFoundError("No se encontró código de verificación para este número")

        verification = response.data[0]

        # Check if expired
        expires_at = datetime.fromisoformat(verification["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
            raise CodeExpiredError("El código ha expirado. Solicita uno nuevo.")

        # Check max attempts
        if verification["attempts"] >= verification["max_attempts"]:
            raise MaxAttemptsExceededError(
                "Demasiados intentos fallidos. Solicita un nuevo código."
            )

        # Verify code (timing-safe comparison)
        if not secrets.compare_digest(verification["code"], code):
            # Increment attempts
            new_attempts = verification["attempts"] + 1
            self.supabase.table("phone_verification_codes").update({
                "attempts": new_attempts
            }).eq("id", verification["id"]).execute()

            attempts_remaining = verification["max_attempts"] - new_attempts
            raise InvalidCodeError(
                f"Código incorrecto. Te quedan {attempts_remaining} intentos."
            )

        # Code is correct - mark as verified
        self.supabase.table("phone_verification_codes").update({
            "verified_at": datetime.utcnow().isoformat()
        }).eq("id", verification["id"]).execute()

        logger.info(f"✅ Code verified successfully for {phone_number}")

        # Create or get user (returns user_dict, email, one_time_password)
        user, email, one_time_password = await self._create_or_get_user(phone_number)

        return {
            "user": user,  # user dict with id, phone, email, created_at
            "email": email,  # Email for Supabase auth
            "password": one_time_password,  # One-time password for frontend to use ONCE
        }

    async def _check_rate_limit(self, phone_number: str) -> None:
        """
        Check if phone number has exceeded rate limit.

        Args:
            phone_number: Phone number to check

        Raises:
            ValueError: If rate limit exceeded
        """
        cooldown_time = datetime.utcnow() - timedelta(seconds=self.cooldown_seconds)

        response = self.supabase.table("phone_verification_codes").select("id").eq(
            "phone_number", phone_number
        ).gte("created_at", cooldown_time.isoformat()).execute()

        if response.data:
            raise ValueError(
                f"Por favor espera {self.cooldown_seconds} segundos antes de solicitar otro código."
            )

    async def _create_or_get_user(
        self,
        phone_number: str,
    ) -> tuple[dict[str, Any], str, str]:
        """
        Create new user or get existing user by phone number.

        Args:
            phone_number: Phone number in E.164 format

        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        # Check if user exists in auth.users by phone
        # Normalize phone number (Supabase stores without + prefix)
        normalized_phone = phone_number.lstrip('+')

        page = 1
        existing_user = None

        logger.info(f"🔍 Searching for user with phone: {phone_number} (normalized: {normalized_phone})")

        while True:
            users_response = self.supabase.auth.admin.list_users(page=page, per_page=1000)

            logger.info(f"📋 Response type: {type(users_response)}")

            # Access the users list from response (handle different response formats)
            users = []
            if hasattr(users_response, 'users'):
                users = users_response.users
                logger.info(f"✅ Found {len(users)} users")
            elif isinstance(users_response, list):
                users = users_response
                logger.info(f"✅ Response is list with {len(users)} users")
            elif isinstance(users_response, dict) and 'users' in users_response:
                users = users_response['users']
                logger.info(f"✅ Found {len(users)} users in dict")

            # Find user with matching phone (compare normalized versions)
            for idx, user in enumerate(users):
                user_phone = getattr(user, 'phone', None)
                # Normalize for comparison
                normalized_user_phone = user_phone.lstrip('+') if user_phone else None
                logger.info(f"👤 User {idx}: phone={user_phone}, match={normalized_user_phone == normalized_phone}")
                if normalized_user_phone == normalized_phone:
                    existing_user = user
                    logger.info(f"✅ MATCH FOUND!")
                    break

            # If found or no more pages, stop
            if existing_user or len(users) < 1000:
                break

            page += 1

        if not existing_user:
            logger.warning(f"⚠️ No existing user found")

        if existing_user:
            # User exists - return one-time password for frontend auth
            user_id = str(existing_user.id)
            email = getattr(existing_user, 'email', None)
            created_at = getattr(existing_user, 'created_at', None)

            logger.info(f"✅ Existing user found: {user_id} (phone: {normalized_phone})")

            # Use temporary email if user doesn't have one
            temp_email = email if email else f"{normalized_phone}@fizko.temp"

            # Generate one-time password for frontend to use
            one_time_password = secrets.token_urlsafe(32)

            # Update user with one-time password (admin API)
            logger.info(f"🔄 Updating user {user_id} with one-time password and confirming email...")
            update_response = self.supabase.auth.admin.update_user_by_id(
                user_id,
                {
                    "password": one_time_password,
                    "email_confirm": True,  # Explicitly confirm email
                }
            )

            # Log the updated user state
            updated_user = update_response.user if hasattr(update_response, 'user') else None
            if updated_user:
                email_confirmed = getattr(updated_user, 'email_confirmed_at', None)
                logger.info(f"✅ User updated - email_confirmed_at: {email_confirmed}")
            else:
                logger.warning(f"⚠️ Update response has no user object")

            logger.info(f"🔐 Updated user {user_id} with one-time password for frontend auth")

            # Return user dict with one-time credentials for frontend
            user_dict = {
                "id": user_id,
                "phone": normalized_phone,
                "email": email,
                "created_at": created_at,
            }

            # Return credentials for frontend to authenticate directly
            return (user_dict, temp_email, one_time_password)

        # Create new user if not found
        else:
            # Create new user
            try:
                # Use temporary email (required for password auth)
                temp_email = f"{normalized_phone}@fizko.temp"

                # Generate one-time password for frontend to use
                one_time_password = secrets.token_urlsafe(32)

                # Create in Supabase Auth with phone, temporary email, and password
                auth_response = self.supabase.auth.admin.create_user({
                    "phone": normalized_phone,
                    "email": temp_email,
                    "password": one_time_password,
                    "phone_confirmed": True,
                    "email_confirmed": True,  # Mark temp email as confirmed
                    "user_metadata": {
                        "verified_via": "whatsapp_otp",
                        "created_via": "whatsapp_login",
                    }
                })

                user_id = str(auth_response.user.id)
                email = auth_response.user.email
                created_at = auth_response.user.created_at

                logger.info(f"✅ New user created: {user_id} (phone: {normalized_phone})")

                # Explicitly confirm email (in case Supabase config overrides the flag)
                logger.info(f"🔄 Explicitly confirming email for new user {user_id}...")
                confirm_response = self.supabase.auth.admin.update_user_by_id(
                    user_id,
                    {
                        "email_confirm": True,
                    }
                )

                # Log confirmation status
                confirmed_user = confirm_response.user if hasattr(confirm_response, 'user') else None
                if confirmed_user:
                    email_confirmed = getattr(confirmed_user, 'email_confirmed_at', None)
                    logger.info(f"✅ Email confirmed - email_confirmed_at: {email_confirmed}")
                else:
                    logger.warning(f"⚠️ Confirmation response has no user object")

                # Return user dict with one-time credentials for frontend
                user_dict = {
                    "id": user_id,
                    "phone": normalized_phone,
                    "email": email,
                    "created_at": created_at,
                }

                # Return credentials for frontend to authenticate directly
                return (user_dict, temp_email, one_time_password)

            except Exception as e:
                logger.error(f"Error creating new user: {e}")
                raise

    def _format_verification_message(self, code: str) -> str:
        """
        Format verification code message for WhatsApp.

        Args:
            code: Six-digit code

        Returns:
            Formatted message string
        """
        return (
            f"🔐 *Código de Verificación Fizko*\n\n"
            f"Tu código es: *{code}*\n\n"
            f"Este código expira en {self.code_expiry_minutes} minutos.\n\n"
            f"_No compartas este código con nadie._"
        )
