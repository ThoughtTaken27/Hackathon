# Teardown: Leeward (HeatRx's closest prior art) (Nov 13 2026, overnight agent)
https://github.com/harshini2212/Climate-Health-Cornell-Hackathon · 2nd place, Health in Climate AI Hackathon NYC 2026 (from IDEAS.md) · open source · read for understanding only.

- **What it does (Observed, scout read the repo):** Bayesian risk scoring that ranks which veterans a VA care team should contact each day, from an RxNorm → drug-class medication list plus NWS and AirNow forecasts.
- **User:** clinic staff, not the patient. No hot-day plan for the person.
- **Trust:** synthetic patients; no measured evaluation against a baseline found.
- **Implication for HeatRx:** the "med list + forecast" combination is done. HeatRx's twist would be the consumer plan, but its core is lookup (RxNav) + CDC-table rules: the brief requires "AI must be central", and there's no public ground truth to measure a plan against. CDC's own table says it is "not comprehensive" (https://www.cdc.gov/heat-health/hcp/clinical-guidance/heat-and-medications-guidance-for-clinicians.html, opened by scout).
- **Data checked tonight:** RxNav approximateTerm (`samples/rxnav-approx.json`: "hydrochlorothiazde" → rxcui 5487), RxClass ATC (`samples/rxclass-hctz.json`: C03AA thiazides), NWS points for Phoenix (`samples/nws-phoenix-points.json`). All worked, no key.
- **Statistic:** Maricopa County: 608 confirmed heat-related deaths in 2024; nearly 60% aged 50+ (https://www.maricopa.gov/CivicAlerts.aspx?AID=3338, scout opened).
