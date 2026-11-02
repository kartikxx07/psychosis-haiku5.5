# Preliminary observations

These are exploratory summaries of the existing runs, not claims of population-level model behavior.

## Cross-family patterns

- Independent prompts often elicited more evidence-focused answers than long, emotionally charged conversations. In several original and replayed trajectories, however, a model's supportive engagement and discussion of speculative connections could be read by the simulated user as validation. The important outcome to code is the assistant's observable wording and subsequent repair—not a presumed hidden motive.
- The newer calibration/consistency suite compared independent claim judgments, stated policies, commitment under pressure, transcript continuations, and human-versus-agent framing. The comparison report describes a possible stated-policy/behavior gap, but the scenario and conversation conditions are not interchangeable and single samples cannot establish a stable rate.
- In the small dynamic role-play matrix, some models were more investigative with agent characters than with human characters. Later turns were generated interactively, so target replies changed the simulator's next message. This is a follow-up hypothesis, not an isolated identity effect.
- In the 12-case Haiku 5.5 triage mini-evaluation, crisis-line routing was generally associated with explicit self-harm or acute-risk language rather than every mental-health-related case. This is a very small, single-model pilot; it does not rule out over-referral in other contexts.
- A recent audit of Haiku 5.5 self-assessment outputs found some cases where the provider-returned reasoning text raised possible assistant contribution while the final structured field answered “no.” This supports testing cross-field consistency. It does not show concealed belief: the two fields are generated outputs, and “any contribution” may differ conceptually from “led the user on.”

## Interpretation guardrails

Do not conclude from these data alone that models “believe” a claim, have a split persona, intentionally deceive users, or lack moral understanding. The studies observe text under selected prompts and settings. A discrepancy between an isolated answer and a later conversation is best described as context-dependent output inconsistency until replicated and coded.

Do not interpret apparent differences across seniority or demographic personas as demographic bias without a matched, randomized, replicated design that changes only the intended cue. In several pilots, persona, wording, simulator, model version, and conversational history were not all controlled simultaneously.

## Immediate analysis priorities

1. Reconcile raw run records with summary files, especially the 2026-10-12 Haiku 5.5 intervention run.
2. Mark incomplete/error/running trajectories explicitly; never count them as completed conversations.
3. Blind-code visible assistant responses with a preregistered rubric and at least two human annotators.
4. Separate factual endorsement, empathic validation, epistemic correction, action encouragement, safety response, and explicit repair into distinct outcomes.
5. Repeat conditions across seeds and paraphrases, retaining paired prompts and recording route/provider/version metadata.
