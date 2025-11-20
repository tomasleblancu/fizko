#!/bin/bash
# Test script for sticky agents functionality
# Usage: ./scripts/test_sticky_agents.sh [backend_url]

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${1:-http://localhost:8089}"
THREAD_ID="test-sticky-$(date +%s)"
TEST_TOKEN="${TEST_JWT_TOKEN:-}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Sticky Agents Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Backend URL: ${YELLOW}${BACKEND_URL}${NC}"
echo -e "Test Thread ID: ${YELLOW}${THREAD_ID}${NC}"
echo ""

# Function to make authenticated request
make_request() {
    local message="$1"
    local headers=(-H "Content-Type: application/json")

    if [ -n "$TEST_TOKEN" ]; then
        headers+=(-H "Authorization: Bearer $TEST_TOKEN")
    fi

    curl -s -X POST "${BACKEND_URL}/chatkit" \
        "${headers[@]}" \
        -d "{
            \"thread_id\": \"${THREAD_ID}\",
            \"text\": \"${message}\"
        }"
}

# Test 1: First message (should use supervisor)
echo -e "${BLUE}Test 1: First Message (Handoff to Specialist)${NC}"
echo -e "Sending: ${YELLOW}'muestra mis facturas del mes pasado'${NC}"
echo ""

RESPONSE1=$(make_request "muestra mis facturas del mes pasado")
echo -e "${GREEN}✓ Request sent${NC}"
echo ""
sleep 2

# Check logs for expected patterns
echo -e "${BLUE}Expected logs:${NC}"
echo -e "  ${YELLOW}👔 [STICKY AGENT] Using supervisor (no active agent)${NC}"
echo -e "  ${YELLOW}📄 [HANDOFF] Supervisor → Tax Documents${NC}"
echo -e "  ${YELLOW}✅ [STICKY AGENT] New: tax_documents_agent${NC}"
echo ""

# Test 2: Second message (should use active agent - STICKY)
echo -e "${BLUE}Test 2: Second Message (Should Use Sticky Agent)${NC}"
echo -e "Sending: ${YELLOW}'cuántas facturas son en total?'${NC}"
echo ""

RESPONSE2=$(make_request "cuántas facturas son en total?")
echo -e "${GREEN}✓ Request sent${NC}"
echo ""
sleep 2

echo -e "${BLUE}Expected logs (CRITICAL):${NC}"
echo -e "  ${GREEN}🎯 [STICKY AGENT] Active: tax_documents_agent${NC}"
echo -e "  ${GREEN}🔄 [STICKY AGENT] Using active agent: Tax Documents Expert${NC}"
echo ""
echo -e "${RED}If you see this instead, sticky agents are NOT working:${NC}"
echo -e "  ${RED}👔 [STICKY AGENT] Using supervisor (no active agent)${NC}"
echo ""

# Test 3: Third message (confirm still sticky)
echo -e "${BLUE}Test 3: Third Message (Confirm Still Sticky)${NC}"
echo -e "Sending: ${YELLOW}'gracias'${NC}"
echo ""

RESPONSE3=$(make_request "gracias")
echo -e "${GREEN}✓ Request sent${NC}"
echo ""
sleep 2

echo -e "${BLUE}Expected logs:${NC}"
echo -e "  ${GREEN}🎯 [STICKY AGENT] Active: tax_documents_agent${NC}"
echo -e "  ${GREEN}🔄 [STICKY AGENT] Using active agent${NC}"
echo ""

# Test 4: Different agent type
echo -e "${BLUE}Test 4: Different Topic (Should Trigger New Handoff)${NC}"
echo -e "Sending: ${YELLOW}'ayúdame con el formulario 29'${NC}"
echo ""

RESPONSE4=$(make_request "ayúdame con el formulario 29")
echo -e "${GREEN}✓ Request sent${NC}"
echo ""
sleep 2

echo -e "${BLUE}Expected logs (if return-to-supervisor enabled):${NC}"
echo -e "  ${YELLOW}🔄 [HANDOFF] Agent → Supervisor${NC}"
echo -e "  ${YELLOW}🧹 [STICKY AGENT] Cleared: tax_documents_agent${NC}"
echo -e "  ${YELLOW}📋 [HANDOFF] Supervisor → Monthly Taxes${NC}"
echo ""
echo -e "${YELLOW}Note: Return-to-supervisor is currently DISABLED by default${NC}"
echo -e "${YELLOW}So it might stay with tax_documents_agent${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Thread ID used: ${YELLOW}${THREAD_ID}${NC}"
echo ""
echo -e "${BLUE}To check logs:${NC}"
echo ""
echo -e "  # Filter by thread ID"
echo -e "  ${YELLOW}tail -f logs/app.log | grep '${THREAD_ID}'${NC}"
echo ""
echo -e "  # Filter by sticky agent tags"
echo -e "  ${YELLOW}tail -f logs/app.log | grep 'STICKY AGENT'${NC}"
echo ""
echo -e "  # Check for handoffs"
echo -e "  ${YELLOW}tail -f logs/app.log | grep 'HANDOFF'${NC}"
echo ""
echo -e "${GREEN}✓ Test completed!${NC}"
echo ""
echo -e "${BLUE}Interpretation:${NC}"
echo -e "  ✅ If you see ${GREEN}'Using active agent'${NC} in logs → Sticky agents work!"
echo -e "  ❌ If you see ${RED}'Using supervisor'${NC} for 2nd/3rd message → Not working"
echo ""
