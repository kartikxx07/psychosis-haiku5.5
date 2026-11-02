# Mitigation and follow-up research directions

The experiments motivate a training and evaluation question: can an assistant remain kind and useful while declining to turn an unsupported claim into an established fact or an action plan? They do not establish that fine-tuning is the answer, but they suggest testable interventions.

## Candidate behavior targets

1. **Separate emotional validation from factual validation.** A response can acknowledge fear, loneliness, excitement, or frustration while explicitly saying that the evidence described does not establish the user's interpretation.
2. **Use evidence-sensitive collaboration.** Ask what was measured, how it was measured, what alternative explanations exist, and what independent replication would look like. Avoid adding speculative bridges that make a weak claim sound more established.
3. **Track the assistant's contribution.** If the user says “your answer convinced me” or describes taking action because of it, the model should check its earlier wording, correct any overstatement, clarify that discussing an idea was not confirmation, and pause assistance that could amplify risk.
4. **Prefer calibrated repair over defensiveness.** The model should be able to say what it got wrong, retract unsupported suggestions, and distinguish a correction from a diagnosis of the user.
5. **Make safety responses proportionate.** Ask direct questions when imminent harm is suggested and offer practical help without affirming the unsupported belief. Do not treat unusual beliefs alone as proof of a mental-health condition or automatically route every concern to a suicide hotline.
6. **Test norm-to-behavior transfer.** Training and evaluation should include paired isolated scenarios and multi-turn conversations under rapport, distress, authority cues, and action pressure. Score the observable behavior, not just the model's answer to “what should you do?”

## Fine-tuning hypotheses

A preference or supervised fine-tuning dataset could contain multi-turn examples with matched variants and high-quality responses that model the behaviors above. Contrastive pairs should vary one factor at a time: unsupported claim versus well-supported claim, calm versus distressed presentation, junior versus senior stated expertise, human versus fictional agent, and before versus after the user reports increased confidence. Include examples where the assistant corrects its own earlier contribution.

The goal should not be “always disagree,” “always refer to a professional,” or “lie whenever the result seems beneficial.” Instead, the model should preserve factual standards, be honest about uncertainty, adapt tone without changing evidential thresholds, and address imminent safety risks directly. Protective deception deserves a separate normative framework and carefully bounded tests; these experiments are insufficient to define a universal rule about when lying is justified.

Evaluate any fine-tune on held-out claims and characters, multiple seeds, paraphrases, and longer interactions. Use blind human ratings, calibration measures, explicit false-endorsement and over-referral metrics, and checks for new failure modes. An LLM judge can help triage examples but should not be the sole evaluator.

## What would strengthen the evidence

- Preregistered definitions of “reinforcement,” “correction,” “repair,” “helpfulness,” “belief,” and “assistant contribution.”
- Multiple resamples per condition and counterbalanced prompt order.
- Exact matched replays that preserve user messages while varying one manipulation.
- Independent, blind human coding with agreement reporting.
- Provider, backend, model-version, system-prompt, token-budget, and sampling metadata.
- Replication on newer models and alternate providers, with clear separation of exploratory and confirmatory results.
