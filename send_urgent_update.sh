#!/bin/bash

# Send Urgent LLM Service Recovery Update
# Date: 2025-07-06

echo "=== Sending Urgent LLM Service Recovery Update ==="
echo ""

# File containing the update
UPDATE_FILE="/Users/polyversai/Downloads/20250706-klaudiusz-to-team-update-llm-restarted-urgent.md"

# Check if update file exists
if [ ! -f "$UPDATE_FILE" ]; then
    echo "ERROR: Update file not found: $UPDATE_FILE"
    exit 1
fi

echo "📧 Update content:"
echo "===================="
cat "$UPDATE_FILE"
echo "===================="
echo ""

# Tailscale messages for Maciej and Monika
echo "📤 Sending via Tailscale..."
echo ""

# For Maciej (mgbook16)
echo "1. To send to Maciej (mgbook16) via Tailscale:"
echo "   Run this command:"
echo "   tailscale file cp \"$UPDATE_FILE\" mgbook16:"
echo ""

# For Monika (silver-1)
echo "2. To send to Monika (silver-1) via Tailscale:"
echo "   Run this command:"
echo "   tailscale file cp \"$UPDATE_FILE\" silver-1:"
echo ""

# Email for Bartosz
echo "📧 For email to Bartosz (b.fink@libraxis.ai):"
echo ""
echo "3. Copy this command to send via mail (if configured):"
echo "   cat \"$UPDATE_FILE\" | mail -s \"URGENT: LLM Service Restarted - DO NOT LOAD C4AI\" b.fink@libraxis.ai"
echo ""
echo "   Or use this curl command for a mail service API:"
echo "   curl -X POST https://api.your-mail-service.com/send \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"to\": \"b.fink@libraxis.ai\", \"subject\": \"URGENT: LLM Service Restarted - DO NOT LOAD C4AI\", \"body\": \"'$(cat "$UPDATE_FILE" | sed 's/"/\\"/g' | tr '\n' ' ')'\"}'"
echo ""

echo "⚠️  CRITICAL REMINDERS:"
echo "   - Service is back up on port 8555"
echo "   - Running in HTTP mode (no SSL)"
echo "   - DO NOT LOAD c4ai model (causes OOM crash)"
echo "   - Available models: Nemotron-49B, Qwen3-14B, Qwen3-8B, deepseek-coder"
echo ""

echo "✅ Please execute the commands above to notify the team immediately!"