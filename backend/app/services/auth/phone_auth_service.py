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

        # ============================================================================
        # TEMPORARY DEVELOPMENT BYPASS - REMOVE IN PRODUCTION!
        # ============================================================================
        # TODO: Replace this with proper WhatsApp template implementation
        # This bypass sends ALL verification codes to a single test number
        # for development purposes only.
        #
        # Normal flow should use:
        #   await self.kapso.messages.send_template(...)
        # ============================================================================
        TEST_PHONE_NUMBER = "56975389973"
        logger.warning(
            f"⚠️  USING DEVELOPMENT BYPASS: Sending code to {TEST_PHONE_NUMBER} "
            f"instead of {phone_number}"
        )

        try:
            # Find active conversation for test number
            conversations_response = await self.kapso.conversations.list(limit=50)

            # Normalize test phone for comparison
            normalized_test = TEST_PHONE_NUMBER.lstrip("+")

            # Handle different response formats from Kapso API
            conversations = (
                conversations_response.get("data")
                or conversations_response.get("nodes")
                or conversations_response.get("conversations")
                or conversations_response.get("items")
                or []
            )

            logger.info(f"🔍 Searching for test number {normalized_test} in {len(conversations)} conversations")

            conversation_id = None
            for conv in conversations:
                # Get phone number directly from conversation (not from nested contact)
                conv_phone = conv.get("phone_number", "").lstrip("+")
                conv_status = conv.get("status", "")

                logger.debug(f"  - Checking conversation: phone={conv_phone}, status={conv_status}")

                if conv_phone == normalized_test and conv_status == "active":
                    conversation_id = conv["id"]
                    logger.info(f"✅ Found active conversation: {conversation_id} for {normalized_test}")
                    break

            if not conversation_id:
                logger.error(
                    f"❌ No active conversation found for {normalized_test}. "
                    f"Searched {len(conversations)} conversations."
                )
                raise ValueError(
                    f"No active conversation found with test number {TEST_PHONE_NUMBER}. "
                    "Please send a message to the bot first."
                )

            # Send verification code to test conversation
            message = (
                f"⚠️  *[DEV BYPASS - TEST ONLY]* ⚠️\n\n"
                f"🔐 *Código de Verificación Fizko*\n\n"
                f"👤 Usuario solicitante: `{phone_number}`\n"
                f"🔑 Código: *{code}*\n\n"
                f"⏰ Expira en {self.code_expiry_minutes} minutos\n\n"
                f"_Este es un mensaje de desarrollo. En producción, el código se enviará al usuario real._"
            )

            await self.kapso.messages.send_text(
                conversation_id=conversation_id,
                message=message,
            )

            logger.warning(
                f"⚠️  [DEV BYPASS] Verification code sent to TEST NUMBER {TEST_PHONE_NUMBER} "
                f"for user {phone_number}. CODE: {code}"
            )

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

        # Create or get user (returns dict, not object)
        user, access_token, refresh_token = await self._create_or_get_user(phone_number)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "user": user,  # user is already a dict with id, phone, email, created_at
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
        # Check if user exists in profiles table
        profile_response = self.supabase.table("profiles").select("*").eq(
            "phone", phone_number
        ).execute()

        if profile_response.data:
            # User exists - generate magic link to get valid tokens
            profile = profile_response.data[0]
            user_id = str(profile["id"])
            email = profile.get("email")

            logger.info(f"✅ Existing user found: {user_id} ({phone_number})")

            # Generate magic link using Supabase Admin API
            # This creates a valid session in Supabase's database
            # We need to provide an email for the magic link
            temp_email = email if email else f"{phone_number.replace('+', '')}@fizko.temp"

            try:
                link_response = self.supabase.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": temp_email,
                    "options": {
                        "redirect_to": "http://localhost:3000",  # Not used, but required
                    }
                })

                # Extract tokens from the response
                # The response contains: action_link, email_otp, hashed_token, verification_type
                # We need to parse the action_link to get the tokens
                action_link = link_response.action_link

                # Extract token from URL
                import urllib.parse
                parsed_url = urllib.parse.urlparse(action_link)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                token_hash = query_params.get('token', [None])[0]

                if not token_hash:
                    raise ValueError("Failed to extract token from magic link")

                # Use the token to create a session and get proper tokens
                verify_response = self.supabase.auth.verify_otp({
                    "type": "magiclink",
                    "token_hash": token_hash,
                    "email": temp_email,
                })

                access_token = verify_response.session.access_token
                refresh_token = verify_response.session.refresh_token

                # Return user dict with tokens
                user_dict = {
                    "id": user_id,
                    "phone": phone_number,
                    "email": email,
                    "created_at": profile.get("created_at"),
                }

                return (user_dict, access_token, refresh_token)

            except Exception as e:
                logger.error(f"Error generating session for existing user: {e}")
                # Fallback to manual JWT generation if magic link fails
                access_token, refresh_token = self._generate_jwt_tokens(user_id, phone_number, email)

                user_dict = {
                    "id": user_id,
                    "phone": phone_number,
                    "email": email,
                    "created_at": profile.get("created_at"),
                }

                return (user_dict, access_token, refresh_token)

        else:
            # Create new user
            try:
                # Use temporary email for new user (required for magic link)
                temp_email = f"{phone_number.replace('+', '')}@fizko.temp"

                # Create in Supabase Auth
                auth_response = self.supabase.auth.admin.create_user({
                    "phone": phone_number,
                    "email": temp_email,
                    "phone_confirmed": True,
                    "email_confirmed": True,  # Mark temp email as confirmed
                    "user_metadata": {
                        "verified_via": "whatsapp_otp",
                        "created_via": "whatsapp_login",
                    }
                })

                user_id = str(auth_response.user.id)
                email = auth_response.user.email

                # Create profile (triggers should handle this, but we'll be explicit)
                self.supabase.table("profiles").insert({
                    "id": user_id,
                    "phone": phone_number,
                }).execute()

                logger.info(f"✅ New user created: {user_id} ({phone_number})")

                # Generate magic link to create a valid session
                try:
                    link_response = self.supabase.auth.admin.generate_link({
                        "type": "magiclink",
                        "email": temp_email,
                        "options": {
                            "redirect_to": "http://localhost:3000",  # Not used, but required
                        }
                    })

                    # Extract token from URL
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(link_response.action_link)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    token_hash = query_params.get('token', [None])[0]

                    if not token_hash:
                        raise ValueError("Failed to extract token from magic link")

                    # Use the token to create a session and get proper tokens
                    verify_response = self.supabase.auth.verify_otp({
                        "type": "magiclink",
                        "token_hash": token_hash,
                        "email": temp_email,
                    })

                    access_token = verify_response.session.access_token
                    refresh_token = verify_response.session.refresh_token

                    # Return user dict with tokens
                    user_dict = {
                        "id": user_id,
                        "phone": phone_number,
                        "email": email,
                        "created_at": auth_response.user.created_at,
                    }

                    return (user_dict, access_token, refresh_token)

                except Exception as e:
                    logger.error(f"Error generating session for new user: {e}")
                    # Fallback to manual JWT generation if magic link fails
                    access_token, refresh_token = self._generate_jwt_tokens(user_id, phone_number, email)

                    user_dict = {
                        "id": user_id,
                        "phone": phone_number,
                        "email": email,
                        "created_at": auth_response.user.created_at,
                    }

                    return (user_dict, access_token, refresh_token)

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
