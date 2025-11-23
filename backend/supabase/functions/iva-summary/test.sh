#!/bin/bash

# Test script for iva-summary edge function
# Usage: ./test.sh [local|staging|prod]

ENV=${1:-local}

case $ENV in
  local)
    FUNCTION_URL="http://localhost:54321/functions/v1/iva-summary"
    ;;
  staging)
    FUNCTION_URL="https://YOUR_STAGING_PROJECT_REF.supabase.co/functions/v1/iva-summary"
    ;;
  prod)
    FUNCTION_URL="https://YOUR_PROD_PROJECT_REF.supabase.co/functions/v1/iva-summary"
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Usage: ./test.sh [local|staging|prod]"
    exit 1
    ;;
esac

# Get JWT token from environment or prompt
if [ -z "$SUPABASE_JWT" ]; then
  echo "Please set SUPABASE_JWT environment variable with your JWT token"
  echo "Example: export SUPABASE_JWT='your-token-here'"
  exit 1
fi

# Get company_id from environment or use default
COMPANY_ID=${COMPANY_ID:-"your-company-id-here"}

# Get period from argument or use current month
PERIOD=${2:-$(date +%Y-%m)}

echo "Testing IVA Summary Edge Function"
echo "=================================="
echo "Environment: $ENV"
echo "URL: $FUNCTION_URL"
echo "Company ID: $COMPANY_ID"
echo "Period: $PERIOD"
echo ""

# Make request
curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -d "{
    \"company_id\": \"$COMPANY_ID\",
    \"period\": \"$PERIOD\"
  }" \
  -w "\n\nStatus: %{http_code}\nTime: %{time_total}s\n" | jq '.'
