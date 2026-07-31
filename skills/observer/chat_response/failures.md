# Failures — Chat Response Generation

## Known Failure Patterns

### 1. Static Template Response
**Symptom:** Same response regardless of input
**Cause:** Default case in response generator catches everything
**Fix:** Add more specific handlers before default case
**Result:** Responses now vary based on content

### 2. Echo Response
**Symptom:** User's input is repeated back with minor changes
**Cause:** Response generator uses user input as template filler
**Fix:** Generate responses from extracted intent, not user input
**Result:** Responses are original, not echoes

### 3. Generic Fallback
**Symptom:** "Want me to take action or keep discussing?" on every response
**Cause:** Hardcoded fallback at end of every response
**Fix:** Only include call-to-action when appropriate
**Result:** Responses end naturally

### 4. Missing Context
**Symptom:** Responses don't reference current system state
**Cause:** Response generator doesn't have access to system status
**Fix:** Inject system state into response context
**Result:** Responses include relevant status information
