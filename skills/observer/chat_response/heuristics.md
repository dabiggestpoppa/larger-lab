# Heuristics — Chat Response Generation

## Intent Classification

| Intent | Keywords | Response Type |
|--------|----------|---------------|
| Status inquiry | "status", "how is", "what's the" | Provide component status |
| Action request | "build", "create", "fix", "update" | Acknowledge + plan |
| Question | "what", "how", "why", "when", "where" | Direct answer |
| Greeting | "hello", "hi", "hey" | Brief acknowledgment |
| Clarification | "what do you mean", "explain" | Elaborate on previous topic |
| Feedback | "good", "bad", "wrong", "right" | Acknowledge + adjust |

## Response Variation Rules

1. Never start with "Got it —" more than once per conversation
2. Never use "I'm processing this through the observer field" — ever
3. Vary sentence length: alternate short and long sentences
4. Include specific details (numbers, names, statuses) when available
5. End with a question or call-to-action only when appropriate

## Content Extraction

- Extract component names (e.g., "vault writer", "compressor", "linker")
- Extract phase references (e.g., "Phase 0A", "Phase 00")
- Extract agent names (e.g., "CC1", "AS", "PM")
- Extract status indicators (e.g., "complete", "pending", "failed")
