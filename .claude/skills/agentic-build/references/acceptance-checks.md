# Risk-based acceptance checks

Pick only the checks that match the changed behaviour; don't turn a small fix into a full-system audit.

| Risk | Invariant to establish | Useful failure case |
|---|---|---|
| External APIs and integrations | Every call has a timeout, one retry and a cached fallback; retries don't duplicate effects; failure leaves recoverable state | Network off; timeout; rate-limit (429); malformed response |
| Cache / no-key mode | The app runs end to end from `demo_cache/` with no API keys | Fresh clone with keys unset; cache miss on a new input |
| LLM output | Output is constrained to supplied facts, returned as JSON, validated, with a template fallback (AGENTS.md §5) | Invalid JSON; extra fields; a fact not in the input; empty reply |
| Safety rules | Unknown inputs are reported as "not in our list", never "safe"; no advice to stop or change a medication | Misspelled name; brand vs generic; an item missing from the table |
| Evaluation | Test set frozen and never tuned on; numbers come only from `python -m eval` | Duplicate examples across splits; labels edited after seeing outputs |
| Persistence and files | Saved state survives a rerun without losing valid data | Rerun; empty state; old cache format |
| Dates and times | Stored, displayed and requested times mean the same moment | Midnight boundary; timezone conversion |
| Release | What judges run (fresh clone or Colab "Run all"), not just a local build, satisfies the contract | Fresh environment; pinned requirements; README steps followed literally |

For each selected risk, keep a compact row: requirement, verifier, observed result, remaining gap.

A green build proves compilation, not correct behaviour, trustworthy sources, a working fresh clone, or good visual design.
