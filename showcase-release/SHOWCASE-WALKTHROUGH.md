# 5-minute LUMEN showcase walkthrough

Use the local runtime for a repeatable product walkthrough. All examples below use synthetic records.

1. **Command centre** — point out the summary metrics, 12-month sample trend, offence-category distribution, district indicators and coordinate preview.
2. **Case registry** — search `Vehicle Theft` or filter to `Mysuru`. Open a `DEMO-FIR-*` row to show the structured dossier, incident metadata and linked entities.
3. **Network intelligence** — show the co-occurrence graph. Select an entity node to open its dossier and inspect linked cases and link-confidence values. Explain that a link is a lead, not an identity finding.
4. **Geospatial** — show the Karnataka-region coordinate plot. State clearly that the points are generated around district reference coordinates, not actual incident locations.
5. **Insights & forecasts** — explain that district scores and volume deviations are descriptive heuristics for this showcase, not validated crime predictions.
6. **Intelligence assistant** — try `Which district has the highest case count?` and inspect the evidence chips. Then try `Compare cases by caste` to demonstrate the protected-attribute refusal.
7. **Data quality & trust / Audit activity** — close by showing the explicit no-auth local-demo boundary, synthetic-data classification and recorded local events.

## Suggested technical narrative

LUMEN separates case records, entity links, graph projections, analytical signals and evidence retrieval. The demo compresses that idea into a local runnable path so reviewers can inspect the workflow without cloud credentials. The upstream Catalyst/QuickML deployment remains a separate integration and validation task.
