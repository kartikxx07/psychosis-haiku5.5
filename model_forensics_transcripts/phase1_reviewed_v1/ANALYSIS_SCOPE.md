# Phase 1 and Phase 2 analysis scope

Include only these completed model blocks:

- `openrouter/deepseek/deepseek-v4-flash`: 61 complete records
- `openrouter/anthropic/claude-haiku-4.5`: 61 complete records

Total included records: **122**. This consists of the 70 Phase 1 records and 52
Phase 2 records.

All 122 included raw files contain a non-empty final answer and a separately stored
provider-returned reasoning field. Three Phase 1 DeepSeek requests initially used
the full 2,000-token allowance for reasoning and were rerun at a 4,000-token ceiling.
One Phase 2 DeepSeek request used the full 4,000-token allowance for reasoning and
was rerun at an 8,000-token ceiling. The corresponding raw/Markdown files contain
the complete replacements, and their per-record metadata identifies the ceiling.

OpenRouter reported a total cost of approximately **$0.6128** for the 122 final,
included response files: approximately $0.03038 for DeepSeek and $0.58245 for
Haiku. This excludes failed transport attempts and superseded empty-answer
responses.

Do not include the partial Gemma block in comparisons. It contains 2 successful
requests and 17 failed attempts caused by OpenRouter/free-upstream HTTP 429 limits.
Those are transport artifacts, not model responses. No Inkling requests were sent.

The authoritative included outputs are the JSON files under `raw/` and the readable
copies under `markdown/` for the two models listed above. The manifest intentionally
retains failed and interrupted attempts for provenance.
