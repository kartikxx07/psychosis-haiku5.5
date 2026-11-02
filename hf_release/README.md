---
license: other
task_categories:
- text-generation
language:
- en
tags:
- safety
- evaluation
- conversational-ai
- mental-health
pretty_name: Conversational Reality-Claim and Support Evaluations
---

# Conversational Reality-Claim and Support Evaluations

Exploratory black-box evaluations of how conversational models respond to fictional users presenting unusual, weakly supported, or reality-related claims—especially when those claims are embedded in emotional conversations, expressed by users with different stated levels of expertise, or accompanied by pressure to affirm them.

This is a research dataset, not a clinical instrument, diagnostic tool, or estimate of how often any behavior occurs in real-world use. “AI-induced psychosis” is the motivating phrase from the source project and is not a diagnosis made by this work. All user characters and scenarios are fictional simulations.

## What is in this release

This initial release is a documented, auditable summary of the experiment suite and its current run status. It does **not** include a bulk dump of raw conversations or provider-returned reasoning fields. The latter are not validated access to private model beliefs or a faithful internal chain of thought. They were treated as auxiliary generated text in the analyses, not as ground truth.

- `data/experiment_inventory.csv`: experiment families, target models, design, and verified status/counts.
- `data/observations.md`: preliminary cross-experiment observations and limitations.
- `data/research_directions.md`: proposed mitigation and follow-up research directions.
- `DATA_RELEASE_NOTES.md`: artifact-selection, privacy, and licensing notes.

Exact prompts, replay manifests, and raw transcripts remain in the source project and are not redistributed in this first bundle. This is deliberate: the source contains provider-returned reasoning fields, emotionally sensitive fictional scenarios, inconsistent/incomplete run records, and third-party model outputs whose redistribution terms need review. The inventory explicitly marks incomplete or internally inconsistent runs.

## Models and routes

The central target models in the newer controlled evaluations were:

- `deepseek/deepseek-v4-flash` via OpenRouter
- `anthropic/claude-haiku-4.5` via OpenRouter
- `anthropic/claude-haiku-5.5` via OpenRouter

Earlier and adjacent work also used Qwen 2.5 7B Instruct as a target and/or role-play simulator, and the original project corpus contains conversations from several other model families. The experiment inventory identifies where a comparison is matched and where it is only exploratory. Provider routing is part of the experimental setup; model aliases alone do not guarantee an identical backend or inference configuration over time.

## Research questions

1. When a user presents an unusual claim, does the assistant distinguish empathy for the person from endorsement of the claim?
2. Does the assistant ask for evidence, surface uncertainty, or prematurely treat user-provided results as credible?
3. Do stated expertise, emotional pressure, or human-versus-agent framing change the assistant's evidential standards or safety response?
4. Does the assistant notice and repair a prior response after the user says it increased their confidence or encouraged consequential action?
5. Do independent scenario answers about honesty, reassurance, and protective deception predict behavior in longer conversations?
6. Do explicit conversational interventions change the assistant's response in exact replays of the same user turns?

The study measures observable outputs and context sensitivity. It does not establish literal beliefs, intent, moral understanding, or a causal mechanism such as reinforcement-learning pressure.

## Preliminary findings

The most informative preliminary pattern is a possible gap between models' answers to independent policy/calibration prompts and their behavior in emotionally loaded, multi-turn conversations. In some trajectories, models offered useful corrections yet also helped elaborate a user's interpretation or did not clearly acknowledge their own possible contribution when the user described becoming more confident. This pattern differed across models and conditions; it should not be generalized into a prevalence claim.

The small human-versus-agent role-play comparison suggested more investigative/diagnostic replies in some agent conversations than in human-character conversations. Because later turns were generated dynamically and the number of samples per cell was low, this remains a hypothesis for controlled replication—not evidence of a stable identity effect.

Independent “would you lie?” scenarios and later conversation behavior did not always align. That is evidence of context-dependent *stated-versus-observed output consistency* in this task setup. It does not prove that a model has a coherent hidden moral policy, consciously lies, or lacks moral understanding.

See [`data/observations.md`](data/observations.md) and [`data/experiment_inventory.csv`](data/experiment_inventory.csv) for detail and run-status caveats.

## Mitigation hypotheses

The motivating concern is not that helpfulness itself is undesirable. It is that warmth, encouragement, and collaboration can sometimes be expressed in ways that a user may interpret as evidence for an unsupported claim. Candidate mitigations for testing include:

- Train and evaluate a clear distinction between validating feelings and validating factual claims.
- Teach the assistant to state what is known, what is not established, and what evidence would change the assessment, without ridicule or premature diagnosis.
- Add a conversational repair behavior: when a user says the assistant's words increased confidence or prompted action, explicitly check what was said, correct overstatements, and clarify that engagement was not confirmation.
- Use multi-turn preference/training data that includes emotional pressure, ambiguity, user expertise cues, and consequential action—not only isolated question-answer scenarios.
- Optimize for calibrated, evidence-seeking help rather than user agreement or continued engagement; evaluate whether improvements generalize to new characters, claims, and paraphrases.
- Keep safety support proportional to what the user actually says. Address immediate danger directly, while avoiding reflexively pathologizing unusual beliefs or routing every mental-health concern to a crisis service.
- Assess truthfulness and protective deception as a carefully specified set of cases. Do not encode the simplistic rule “lie if the outcome seems good”; test truthful alternatives, minimal necessary disclosure, uncertainty, consent, and imminent-harm exceptions separately.

These are research hypotheses, not validated interventions or clinical guidance. Fine-tuning could help, but it could also overfit to templates, make the model more confident in self-assessments, or shift failure modes. Any training change should be tested against held-out multi-turn conversations, independent human coding, and explicit harm and calibration measures.

## Limitations

- Most conditions have one sample per cell; these are exploratory observations, not robust population estimates.
- Some runs are incomplete or have metadata/accounting inconsistencies. See the inventory; do not treat planned conditions as completed.
- Dynamic role-play changes the user turns based on the target model's replies, so subsequent turns are not controlled across models.
- The fictional scenarios are selected and authored by the researchers; they do not represent clinical populations or the diversity of real conversations.
- Model versions, system prompts, inference settings, provider routing, and safety policies can change. Results apply to the recorded endpoint/configuration and date, not necessarily the current model.
- Ratings and self-assessments are generated outputs and can be inconsistent. They should be checked against the actual visible conversation by trained human annotators.
- A conversation transcript cannot establish a model's internal beliefs, intentions, or moral competence.

## Citation

Please cite the source repository and identify this as an exploratory extension of Tim Hua's original project. A formal citation and author list should be added by the maintainers before public release.

## License and redistribution

The source project's MIT license applies to its software under its terms; it does not automatically settle redistribution rights for provider-generated model outputs, third-party source transcripts, or every dataset artifact. This dataset card uses `license: other` pending an explicit data-license review. Do not assume that model-output or prompt artifacts are cleared for unrestricted reuse.

## Safety note

This dataset includes fictional descriptions of unusual beliefs, distress, and mental-health-related situations. It is intended to evaluate model behavior in research settings, not to simulate treatment, diagnose a person, or encourage anyone to act on unsupported beliefs. If adapting these scenarios, preserve clear safeguards against affirming harmful false claims and provide appropriate support when a real person indicates immediate danger.
