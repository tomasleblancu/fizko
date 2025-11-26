# WhatsApp Template Setup for Phone Authentication

## Overview

Phone authentication via WhatsApp OTP requires a **pre-approved WhatsApp template**. Regular text messages cannot be sent to users who haven't initiated a conversation first. Templates bypass this restriction and can start new conversations.

## Required Template

### Template Details

**Template Name**: `authentication_code` (configurable via `PHONE_VERIFICATION_TEMPLATE_NAME`)

**Category**: AUTHENTICATION

**Language**: Spanish (`es`) - configurable via `PHONE_VERIFICATION_TEMPLATE_LANGUAGE`

**Parameters**: 1 parameter (the 6-digit verification code)

### Recommended Template Content

**Header**: None (or "Código de Verificación")

**Body**:
```
Tu código de verificación es: {{1}}

Este código expira en 5 minutos. No lo compartas con nadie.
```

**Footer**: "Fizko - Contabilidad Inteligente"

**Buttons**: None (or optional "Copy Code" button if supported)

## Setup Steps

### 1. Create Template in Kapso Dashboard

1. Log in to [Kapso Dashboard](https://app.kapso.ai)
2. Navigate to **WhatsApp Templates**
3. Click **Create New Template**
4. Fill in the details:
   - **Name**: `authentication_code`
   - **Category**: AUTHENTICATION
   - **Language**: Spanish (es_CL or es)
   - **Body**: Use the recommended content above
   - **Parameters**: 1 parameter for the code

### 2. Submit for WhatsApp Approval

1. Review the template content
2. Submit for WhatsApp approval
3. Wait for approval (usually 15 minutes to 24 hours)
4. Check approval status in Kapso dashboard

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# WhatsApp Template Configuration
PHONE_VERIFICATION_TEMPLATE_NAME=authentication_code
PHONE_VERIFICATION_TEMPLATE_LANGUAGE=es

# Or use custom template name if different
# PHONE_VERIFICATION_TEMPLATE_NAME=your_custom_template_name
```

## Testing

Once the template is approved, you can test phone authentication:

```bash
# Request verification code
curl -X POST http://localhost:8000/api/auth/phone/request-code \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+56912345678"}'

# Verify code
curl -X POST http://localhost:8000/api/auth/phone/verify-code \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+56912345678", "code": "123456"}'
```

## Alternative: Use Existing Template

If you already have an AUTHENTICATION template in Kapso:

1. List your templates:
```bash
# Using Kapso MCP (if available)
# Or via Kapso API directly
```

2. Update environment variable to use your template:
```bash
PHONE_VERIFICATION_TEMPLATE_NAME=your_existing_template_name
```

3. Ensure the template has exactly 1 parameter for the verification code

## Troubleshooting

### Template Not Found

**Error**: `Template 'authentication_code' not found`

**Solution**:
1. Check template name matches exactly (case-sensitive)
2. Verify template is approved by WhatsApp
3. Confirm template exists in your Kapso project

### Template Rejected

**Error**: Template submission rejected by WhatsApp

**Common reasons**:
- Body text too long (max 1024 characters)
- Contains prohibited content (URLs, phone numbers)
- Doesn't follow WhatsApp guidelines for AUTHENTICATION category

**Solution**: Review [WhatsApp Business Template Guidelines](https://developers.facebook.com/docs/whatsapp/message-templates/guidelines)

### Wrong Number of Parameters

**Error**: `Template parameter mismatch`

**Solution**: Ensure template has exactly 1 parameter (`{{1}}`) for the verification code

## Production Checklist

- [ ] Template created in Kapso dashboard
- [ ] Template approved by WhatsApp (status: APPROVED)
- [ ] Template category is AUTHENTICATION
- [ ] Template has exactly 1 parameter
- [ ] Environment variables configured
- [ ] Backend server restarted
- [ ] Test with real phone number
- [ ] Verify code delivery (<30 seconds)
- [ ] Confirm code verification works

## Notes

- **Template approval time**: 15 minutes to 24 hours
- **Cost**: AUTHENTICATION templates are typically free or low-cost
- **Rate limits**: Same as other WhatsApp messages (80 msg/sec per phone number)
- **Language**: Must match the user's WhatsApp language preference for best delivery

## Support

If you need help:
1. Check Kapso dashboard for template status
2. Review WhatsApp Business API logs
3. Contact Kapso support for template issues
4. See [backend/WHATSAPP_AUTH_ARCHITECTURE.md](WHATSAPP_AUTH_ARCHITECTURE.md) for implementation details
