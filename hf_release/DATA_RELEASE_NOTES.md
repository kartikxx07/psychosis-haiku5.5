# Data release notes

This first Hugging Face-ready bundle contains documentation and an experiment inventory only. It does not redistribute raw conversation transcripts, raw API records, hidden/provider-returned reasoning fields, API credentials, or local environment/configuration files.

Reasons for this conservative first release:

- Some records contain provider-returned reasoning. Those records are not a validated window into private beliefs and should not be presented as ground truth.
- Some runs have incomplete trajectories or summary/count discrepancies that need reconciliation before release as benchmark data.
- The source corpus contains emotionally sensitive fictional scenarios and third-party model outputs; redistribution permissions and data licensing need review.
- The existing software license does not necessarily grant rights over all generated outputs or third-party material.

The inventory distinguishes verified completed runs from partial, incomplete, or unresolved artifacts. Do not infer completion from a compiled input manifest alone.

Before expanding this release, maintainers should: audit and normalize run metadata; verify source and output licensing; remove provider reasoning and credentials; preserve complete visible user/assistant turns with provenance; and publish a versioned schema plus checksums.
