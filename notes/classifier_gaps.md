# Classifier v3 suspected gaps (for the future journal version; v3 is frozen in this paper)

Do not act on these in the IPTC-25544-MS rerun.

1. **Non-ASCII characters not normalised.** `normalise_text` replaces only ½, ¼, ¾, ⅛. The narratives (sum24Hr plus forecast24hr) also contain ³ (31), Ø (13), æ (9), ¿ (3), Æ (2), Å (1). `³` appears in volume units; `Ø` is used as a diameter or "at" symbol (e.g. `Ø 3100M`, `TD Ø 3220 M`) and may hide depth or hole-size context; `¿` (3) looks like a corrupted character in the source. Source: Stage 3 Unicode survey, `outputs/stage3_unicode_survey.csv`.
2. **The "8½" pattern in "Reservoir drilling" (`8½.{0,5}(?:hole|section)`) can never match after normalisation**, because ½ is replaced by " 1/2" first. Suspected, to be confirmed in Stage 4 by checking whether any DDR matches only through that pattern.
