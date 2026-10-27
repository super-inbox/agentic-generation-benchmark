# Archived results and denominators

Recompute the values from the bundled data with `python3 -m draftbench report`. These are descriptive configured-system observations from the existing archive, not new experiments or an overall leaderboard.

## Primary design comparison

| Scope | Planned per system | Astra completed / scored | Claude completed / scored |
|---|---:|---:|---:|
| Brief Bank v0.3 | 43 | 43 / 43 | 35 / 35 |
| Entire design-related archive | 261 | 259 / 260 | 233 / 235 |

Completed and scored are different properties: some timed-out broader-archive runs left scoreable artifacts. Eight Claude Brief Bank first-turn timeouts leave quality unobserved. The 43 conditions correspond to 35 base briefs; the 32 v0.2 historical associations add no new execution. Do not combine task-specific quality metrics across groups into a single mean.

The input tool configurations differ, including built-in image generation for Astra and code/native production for Claude. These results do not isolate model-weight effects. Numeric intervals in the archive preserve unmeasured dimensions and are not statistical confidence intervals or expert acceptance ratings.

## RFQ success at eight customer rounds

| View | Astra | Claude | Sol |
|---|---:|---:|---:|
| Original 20, amended Claude attempts | 17/20 | 18/20 | 11/20 |
| Extension, own scored denominator | 20/20 | 16/19 | No scored runs |
| Extension, common 19 | 19/19 | 16/19 | — |
| Both cohorts, common 39 | 36/39 | 34/39 | — |
| Strict paired 36, removing three original Claude reattempt cases from both systems | 33/36 | 32/36 | — |

On the common 39, Coverage@6 is approximately **80.10% for both systems**; Coverage@8 is **98.90% for Astra** and **98.17% for Claude**. These are case-macro means preserving each original field denominator. Simulator leak rate uses aggregate disclosure counts, not a mean of per-case rates.

The strict view removes 004, 009 and 019, while 028 is already absent from the paired scored intersection because of a Claude infrastructure interruption. The two cohorts differ in router/auditor configurations and continuation histories; exclusions do not fully match the experimental conditions. Coverage and success measure elicitation, not final-brief acceptance or downstream design usefulness.

## Separate R1 pilot

Seven historical Sol/Astra pairs were rejudged with revised acceptance rules in two opposite anonymous presentations, totaling fourteen judge calls. Three pairs vary between presentations. TIQ-100's Sol score differs by 30 points across its two calls; its arithmetic average is not a stable expert verdict. Claude does not participate.

R1 changes neither candidate outputs nor historical aggregate scores. Expert adjudication is pending, so neither R1 nor the selected case inspections support an overall evaluator false-positive/false-negative rate.
