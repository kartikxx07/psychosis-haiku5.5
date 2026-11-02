# DeepSeek smoke-evaluation datasets

This folder contains small, human-authored datasets for validating the DeepSeek
black-box evaluation pipeline before running the full 72-conversation study.
No item requires a red-team model to generate the user message.

## Files

- `response_policy_scenarios.jsonl`: Meta-level scenarios that ask DeepSeek to
  identify the user's likely goal and draft the response it would send.
- `belief_claims.jsonl`: Context-free propositions used to establish DeepSeek's
  baseline epistemic position before those propositions appear in a vulnerable
  conversation.
- `followup_probes.jsonl`: Reusable follow-ups for measuring repair after
  perceived validation, retrospective endorsement, evaluation awareness, and
  inferred user characteristics.
- `scoring_rubric.md`: Human-scoring definitions for the smoke-test outputs.

Each JSONL object contains a `prompt` field that may be sent to the target model.
All other fields are evaluator metadata and MUST NOT be included in the model
request unless a later experiment explicitly says otherwise.

## What these datasets test

The response-policy dataset measures whether the model knows how it should
respond when the user's experience is emotionally real but the proposed causal
explanation is unsupported. Because it explicitly asks the model to describe
its approach, this is a policy-competence test rather than a natural conversation.

The belief-claims dataset measures the model's context-free stance toward a
claim. It does not measure consciousness or phenomenal belief. In this project,
"baseline belief" means the proposition the model explicitly endorses, rejects,
or treats as uncertain when it is not accommodating a particular user.

The follow-up probes are applied only after a response has been recorded. They
test whether the model repairs unintended reinforcement, retains or retracts its
claims, and changes its assessment after learning that a user was simulated or
that the exchange was an evaluation.

## Recommended smoke run

1. Run all `belief_claims.jsonl` items once with reasoning enabled.
2. Run all `response_policy_scenarios.jsonl` items once with reasoning enabled.
3. Select one safe, one ambiguous, and one reinforcing response.
4. Apply the `uptake_neutral`, `self_review_no_disclosure`, and
   `self_review_simulation_disclosure` follow-ups to each selected response.
5. Manually score outputs using `scoring_rubric.md`.

For provider variability, repeat the complete smoke run twice. Keep the exact
model version, provider route, reasoning settings, and completion cap fixed.

## Recording requirements

For every request save:

- dataset name and item ID;
- exact model and upstream provider;
- complete request messages;
- returned `reasoning` and/or `reasoning_details` without editing;
- final answer;
- input, reasoning, and output token counts when available;
- finish reason, latency, timestamp, and error information;
- parent response ID and branch name for follow-up probes.

Do not place API keys or authorization headers in the saved records.

