"""Phone authentication service using WhatsApp OTP."""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from gotrue import User
from supabase import Client

from app.services.whatsapp import WhatsAppService

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
        self.whatsapp_service = WhatsAppService(supabase)

        # Configuration
        self.code_expiry_minutes = int(os.getenv("PHONE_VERIFICATION_CODE_EXPIRY_MINUTES", "5"))
        self.max_attempts = int(os.getenv("PHONE_VERIFICATION_MAX_ATTEMPTS", "3"))
        self.cooldown_seconds = int(os.getenv("PHONE_VERIFICATION_COOLDOWN_SECONDS", "60"))

    def _generate_code(self) -> str:
        """
        Generate a random 6-digit verification code.

        Returns:
            Six-digit numeric code as string
        """
        # Use secrets for cryptographically secure random numbers
        code = secrets.randbelow(1000000)
        return f"{code:06d}"

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

        # Send code via WhatsApp
        try:
            message = self._format_verification_message(code)
            await self.whatsapp_service.send_text_to_phone(
                phone_number=phone_number,
                message=message,
            )
            logger.info(f"✅ Verification code sent to {phone_number} via WhatsApp")

        except Exception as e:
            logger.error(f"Failed to send verification code via WhatsApp: {e}")
            # Delete the code from database if send fails
            self.supabase.table("phone_verification_codes").delete().eq(
                "id", verification_record.data[0]["id"]
            ).execute()
            raise ValueError(
                f"No se pudo enviar el código por WhatsApp. "
                f"Asegúrate de tener una conversación activa con el número {phone_number}."
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

        # Create or get user
        user, access_token, refresh_token = await self._create_or_get_user(phone_number)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "phone": user.phone,
                "email": user.email,
                "created_at": user.created_at,
            }
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
    ) -> tuple[User, str, str]:
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
            # User exists - get their auth user
            profile = profile_response.data[0]
            user_id = profile["id"]

            # Get or create auth session
            # Use admin API to create session for user
            try:
                # Sign in user with phone (Supabase auth)
                auth_response = self.supabase.auth.admin.create_user({
                    "phone": phone_number,
                    "phone_confirmed": True,
                    "user_metadata": {
                        "verified_via": "whatsapp_otp",
                        "last_login": datetime.utcnow().isoformat(),
                    }
                })

                # Generate access token
                # Note: Supabase admin API doesn't directly give tokens
                # We need to use sign_in or create a session
                # For now, we'll use a workaround with magic link
                link_response = self.supabase.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": f"{phone_number.replace('+', '')}@fizko.temp",
                })

                return (
                    auth_response.user,
                    link_response.properties.access_token,
                    link_response.properties.refresh_token,
                )

            except Exception as e:
                logger.error(f"Error creating auth session: {e}")
                raise

        else:
            # Create new user
            try:
                # Create in Supabase Auth
                auth_response = self.supabase.auth.admin.create_user({
                    "phone": phone_number,
                    "phone_confirmed": True,
                    "user_metadata": {
                        "verified_via": "whatsapp_otp",
                        "created_via": "whatsapp_login",
                    }
                })

                user_id = auth_response.user.id

                # Create profile (triggers should handle this, but we'll be explicit)
                self.supabase.table("profiles").insert({
                    "id": str(user_id),
                    "phone": phone_number,
                }).execute()

                logger.info(f"✅ New user created: {user_id} ({phone_number})")

                # Generate tokens
                link_response = self.supabase.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": f"{phone_number.replace('+', '')}@fizko.temp",
                })

                return (
                    auth_response.user,
                    link_response.properties.access_token,
                    link_response.properties.refresh_token,
                )

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
