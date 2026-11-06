# Research Rules

1. Row `t` may use only information available at bar `t`'s close; targets use later closes ([DEC-006](../decisions/DECISION_LOG.md)).
2. Lifetime engagement/follower counts are not point-in-time: not allowed in primary features; any use must be labelled leaky.
3. News is excluded from the primary model; model D is explicitly separate.
4. No random splits; purge overlapping targets; embargo; tune only inside training windows; never on the final test.
5. Scalers/imputers/normalisers fit on training data only.
6. Report every horizon separately; correct for multiple comparisons; distinguish statistical from economic significance.
7. Do not optimise to produce a positive result; report nulls and failed experiments with the same care.
8. Changing methodology requires a new DEC entry; never silently.
9. Predictions are append-only; each run is a new folder.
10. Separate in reports: observed facts / model predictions / interpretation. Sentiment is not a buy/sell signal without validated trading evidence.
