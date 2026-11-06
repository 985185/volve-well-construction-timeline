# Spud date validation rules (Section 5.6 of the paper)

Rules are applied in the order R1 (inherited), R5a (parent leg) and R5b (technical sidetrack), R2 (error), R3 (later campaign), R4 (exact), R6 (definitional offset), R7 (unresolved). Unresolved includes 15/9-19 S, F-9 and F-11 (R7).

- Exact agreement: R4: WITSML within 1 day of NOD, and the first report or free-text spud follows by at most 1 day.
- Definitional offset: R6: within 8 days of NOD, free-text start 2 to 20 days later. R5a: parent leg whose NOD record belongs to its technical sidetrack, with no free-text spud date.
- WITSML data-entry error: R2: differs from the first report or free-text spud by more than 30 days, while NOD agrees with them within 3 days.
- NOD date marks later campaign: R3: within 7 days of the first report, more than 1 year from NOD.
- Inherited parent spud date: R1: same spud date as the parent.
- Unresolved: R5b: technical sidetrack whose NOD record is its parent leg's. R7: no other rule fits.
