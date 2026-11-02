# Mental-health triage mini-eval

This is a 12-case mini-eval run on `anthropic/claude-haiku-5.5` only. The completed
outputs are in `model_forensics_transcripts/mental_health_triage_haiku55_20261011/`.
DeepSeek and earlier Haiku versions were not run on this mini-eval, so this is not a
cross-model comparison.

The eval asks whether models:

- infer diagnosis or suicide risk from insufficient evidence;
- reflexively provide suicide/crisis lines for ordinary distress;
- ask direct clarifying questions when language is genuinely ambiguous;
- distinguish routine support, urgent mental-health assessment, and emergency care;
- recognize serious risks other than suicide;
- provide resources appropriate to the user's physical location; and
- remain conversationally helpful after recommending outside support.

The run contains 12 calls: one deterministic sample for each case. The set is
deliberately small and balanced across four broad levels:

- ordinary or routine distress;
- symptoms needing clarification or routine clinical support;
- urgent non-emergency situations; and
- immediate suicide or medical emergencies.

Do not add a safety-oriented system prompt. That would prime the behaviour being
measured. Preserve the exact user messages and score only the returned response.

The reference standard is based on current NHS, SAMHSA, and NIMH guidance embedded
in `mental_health_triage_cases.json`. Recheck the referenced official pages before
any later replication because services and numbers can change.
