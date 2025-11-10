#!/bin/bash
# Script to update SII_FAQ_VECTOR_STORE_ID in .env with the latest active vector store

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VECTOR_STORES_JSON="$SCRIPT_DIR/app/integrations/sii_faq/vector_stores.json"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if vector_stores.json exists
if [ ! -f "$VECTOR_STORES_JSON" ]; then
    echo "❌ Error: vector_stores.json not found at $VECTOR_STORES_JSON"
    exit 1
fi

# Extract latest active vector_store_id using Python
LATEST_ID=$(python3 -c "
import json
with open('$VECTOR_STORES_JSON', 'r') as f:
    data = json.load(f)
    active = [vs for vs in data.get('vector_stores', []) if vs.get('status') == 'active']
    if active:
        active.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        print(active[0]['vector_store_id'])
")

if [ -z "$LATEST_ID" ]; then
    echo "❌ Error: No active vector stores found in vector_stores.json"
    exit 1
fi

echo "📚 Latest active SII FAQ vector store: $LATEST_ID"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env file not found, creating it..."
    touch "$ENV_FILE"
fi

# Update or add SII_FAQ_VECTOR_STORE_ID in .env
if grep -q "^SII_FAQ_VECTOR_STORE_ID=" "$ENV_FILE"; then
    # Update existing line
    sed -i.bak "s/^SII_FAQ_VECTOR_STORE_ID=.*/SII_FAQ_VECTOR_STORE_ID=$LATEST_ID/" "$ENV_FILE"
    echo "✅ Updated SII_FAQ_VECTOR_STORE_ID in .env"
else
    # Add new line
    echo "" >> "$ENV_FILE"
    echo "# SII FAQ Vector Store (auto-generated)" >> "$ENV_FILE"
    echo "SII_FAQ_VECTOR_STORE_ID=$LATEST_ID" >> "$ENV_FILE"
    echo "✅ Added SII_FAQ_VECTOR_STORE_ID to .env"
fi

echo ""
echo "🎉 Done! Vector store ID configured:"
echo "   $LATEST_ID"
echo ""
echo "💡 Restart your backend to apply changes:"
echo "   ./dev.sh"
