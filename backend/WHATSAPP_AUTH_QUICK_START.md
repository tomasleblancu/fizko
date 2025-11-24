# WhatsApp Phone Authentication - Quick Start

## What Changed

The phone authentication system now uses **WhatsApp Templates** instead of regular text messages. This is required because WhatsApp Business API doesn't allow sending regular messages to users who haven't initiated a conversation first.

## Files Modified

1. **Kapso Integration**:
   - Added `send_template()` method to [app/integrations/kapso/api/messages.py](app/integrations/kapso/api/messages.py)

2. **Phone Auth Service**:
   - Updated [app/services/auth/phone_auth_service.py](app/services/auth/phone_auth_service.py)
   - Now uses `KapsoClient` instead of `WhatsAppService`
   - Sends verification codes via WhatsApp templates

3. **Documentation**:
   - Created [WHATSAPP_TEMPLATE_SETUP.md](WHATSAPP_TEMPLATE_SETUP.md) - Template setup guide

## Required Setup (IMPORTANT!)

### 1. Create WhatsApp Template in Kapso

You MUST create and get approval for a WhatsApp template before phone authentication will work.

**Quick Steps**:
1. Go to Kapso Dashboard → WhatsApp Templates
2. Create template named `authentication_code` (or custom name)
3. Category: **AUTHENTICATION**
4. Language: Spanish (es)
5. Body content:
   ```
   Tu código de verificación es: {{1}}

   Este código expira en 5 minutos. No lo compartas con nadie.
   ```
6. Submit for WhatsApp approval
7. Wait for approval (15 min - 24 hours)

**Full guide**: See [WHATSAPP_TEMPLATE_SETUP.md](WHATSAPP_TEMPLATE_SETUP.md)

### 2. Environment Variables

Add to your `.env` file:

```bash
# Required - Kapso API credentials
KAPSO_API_KEY=your_kapso_api_key

# Optional - Template configuration
PHONE_VERIFICATION_TEMPLATE_NAME=authentication_code
PHONE_VERIFICATION_TEMPLATE_LANGUAGE=es

# Optional - Verification settings
PHONE_VERIFICATION_CODE_EXPIRY_MINUTES=5
PHONE_VERIFICATION_MAX_ATTEMPTS=3
PHONE_VERIFICATION_COOLDOWN_SECONDS=60
```

### 3. Restart Backend

After template is approved and environment variables are set:

```bash
# Docker
docker-compose restart backend

# Or local
cd backend
./dev.sh
```

## Testing

### 1. Check Template Status

First, verify your template is approved in the Kapso dashboard.

### 2. Request Verification Code

```bash
curl -X POST http://localhost:8000/api/auth/phone/request-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Código enviado por WhatsApp",
  "expires_at": "2025-11-23T22:10:00.000Z",
  "retry_after": 60
}
```

### 3. Check WhatsApp

You should receive a message on WhatsApp with your verification code.

### 4. Verify Code

```bash
curl -X POST http://localhost:8000/api/auth/phone/verify-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678",
    "code": "123456"
  }'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 3600,
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "+56912345678",
    ...
  }
}
```

## Common Errors

### "Template 'authentication_code' not found"

**Cause**: Template doesn't exist or isn't approved yet

**Solution**:
1. Check Kapso dashboard for template status
2. Ensure template name matches environment variable
3. Wait for WhatsApp approval if still pending

### "KAPSO_API_KEY environment variable is required"

**Cause**: Missing Kapso API key in environment

**Solution**: Add `KAPSO_API_KEY` to your `.env` file

### "No se pudo enviar el código por WhatsApp"

**Cause**: Failed to send template (various reasons)

**Solution**:
1. Check backend logs for detailed error
2. Verify phone number is in E.164 format (+56912345678)
3. Ensure Kapso account has credits/active subscription
4. Check template is approved and active

## Architecture Overview

```
User Request (phone number)
       ↓
POST /api/auth/phone/request-code
       ↓
PhoneAuthService.request_verification_code()
       ↓
1. Check rate limit
2. Generate 6-digit code
3. Save to phone_verification_codes table
4. Send via Kapso template → WhatsApp
       ↓
User receives code on WhatsApp
       ↓
POST /api/auth/phone/verify-code
       ↓
PhoneAuthService.verify_code()
       ↓
1. Find active code in DB
2. Check expiry & attempts
3. Verify code (timing-safe)
4. Create/get user
5. Generate JWT tokens
       ↓
Return access_token + user profile
```

## Next Steps

1. ✅ Create WhatsApp template in Kapso
2. ✅ Get template approved by WhatsApp
3. ✅ Configure environment variables
4. ✅ Restart backend
5. ✅ Test with real phone number
6. 🚀 Implement frontend (see [WHATSAPP_AUTH_FRONTEND_GUIDE.md](WHATSAPP_AUTH_FRONTEND_GUIDE.md))

## Related Documentation

- **Architecture**: [WHATSAPP_AUTH_ARCHITECTURE.md](WHATSAPP_AUTH_ARCHITECTURE.md)
- **Template Setup**: [WHATSAPP_TEMPLATE_SETUP.md](WHATSAPP_TEMPLATE_SETUP.md)
- **Frontend Guide**: [WHATSAPP_AUTH_FRONTEND_GUIDE.md](WHATSAPP_AUTH_FRONTEND_GUIDE.md)
- **Usage Examples**: [WHATSAPP_AUTH_USAGE.md](WHATSAPP_AUTH_USAGE.md)

## Support

If you encounter issues:
1. Check backend logs: `docker logs -f fizko-backend`
2. Review Kapso dashboard for template status
3. Verify environment variables are set correctly
4. Ensure WhatsApp template is approved
5. Check phone number format (E.164: +56912345678)
