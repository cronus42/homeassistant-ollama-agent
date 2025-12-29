# Quick Test Guide - Gemma3 Think Block Fix

## Deploy the Fix

```bash
# From your dev machine (gurathin)
cd ~/repos/homeassistant/homeassistant-ollama-agent
scp -r custom_components/ollama_conversation sanctuarymoon.local:/config/custom_components/
```

## Restart Home Assistant

Option 1: Via UI
- Settings → System → Restart

Option 2: Via SSH
```bash
ssh sanctuarymoon.local "ha core restart"
```

## Enable Debug Logging (Optional but Recommended)

Edit configuration.yaml:
```bash
ssh sanctuarymoon.local
nano /config/configuration.yaml
```

Add this section:
```yaml
logger:
  default: info
  logs:
    custom_components.ollama_conversation: debug
```

Save and restart HA again.

## Test Cases

### Test 1: Turn Off Light
```yaml
service: conversation.process
data:
  text: "Turn off the desk lamp"
  agent_id: conversation.ollama_conversation
```

Expected: "Done! I've turned off light.desk_lamp." OR natural response like "I've turned off the desk lamp."

### Test 2: Turn On Light
```yaml
service: conversation.process
data:
  text: "Turn on the kitchen light"
  agent_id: conversation.ollama_conversation
```

Expected: Natural confirmation without any think tags

### Test 3: Set Temperature
```yaml
service: conversation.process
data:
  text: "Set the bedroom to 72 degrees"
  agent_id: conversation.ollama_conversation
```

Expected: "Done! I've set climate.bedroom to 72°" OR natural response

## Monitor Logs

```bash
# Watch logs in real-time
ssh sanctuarymoon.local "tail -f /config/home-assistant.log | grep ollama"
```

### What to Look For

Good Signs:
- "Filtered think blocks from response" (debug log)
- "Raw response from model:" (shows unfiltered output)
- Clean user-facing responses
- No think tags visible to user

Warning Signs (now handled gracefully):
- "Response was empty after filtering think blocks" - triggers fallback
- Should still get a proper confirmation message

## Verify Fix Success

Success Criteria:
1. User never sees think tags in responses
2. All device control commands get proper confirmations
3. Logs show filtering is working (if debug enabled)
4. Empty filtered responses trigger intelligent fallbacks

Failure (needs more work):
1. User still sees think tags
2. Empty/blank responses
3. Errors in logs

## Rollback (If Needed)

```bash
# Backup old version first, then restore if needed
ssh sanctuarymoon.local "rm -rf /config/custom_components/ollama_conversation"
# Then reinstall previous version
```

## Report Results

After testing, document:
- Which test cases passed/failed
- Any log warnings or errors
- Model behavior (does it still try to use think tags?)
- Fallback response quality
