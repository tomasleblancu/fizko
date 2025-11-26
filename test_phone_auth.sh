#!/bin/bash

# Script de prueba para WhatsApp Phone Authentication
# Uso: ./test_phone_auth.sh +56912345678

BACKEND_URL="http://localhost:8000"
PHONE_NUMBER="${1:-+56975389973}"

echo "========================================="
echo "🧪 Testing WhatsApp Phone Authentication"
echo "========================================="
echo ""
echo "📱 Phone: $PHONE_NUMBER"
echo "🌐 Backend: $BACKEND_URL"
echo ""

# Step 1: Request Code
echo "▶️  PASO 1: Solicitando código de verificación..."
echo ""

RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/phone/request-code" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE_NUMBER\"}")

echo "Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Check if successful
if echo "$RESPONSE" | grep -q '"success".*true'; then
    echo "✅ Código enviado exitosamente!"
    echo ""
    echo "📲 Revisa tu WhatsApp y luego ejecuta:"
    echo ""
    echo "   curl -X POST $BACKEND_URL/api/auth/phone/verify-code \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"phone_number\": \"$PHONE_NUMBER\", \"code\": \"CODIGO_AQUI\"}'"
    echo ""
else
    echo "❌ Error al solicitar código"
    echo ""
    echo "Verifica:"
    echo "  1. El backend está corriendo (./dev.sh)"
    echo "  2. Las variables de entorno están configuradas"
    echo "  3. El template 'wp_verification' está aprobado en Kapso"
    echo ""
fi

echo "========================================="
