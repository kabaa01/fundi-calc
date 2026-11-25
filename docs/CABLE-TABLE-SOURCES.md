# Where the cable table comes from

Fundi Calc picks a breaker and a copper cable for a circuit. The numbers below are published, so anyone can check them.

## The Kenya link
The Kenya wiring standard is KS 662. KEBS published draft updates for public comment from 12 March to 15 May 2026. The draft says it is in line with IEC 60364 and follows the chapters of BS 7671 (18th Edition). It has a section on current-carrying capacity and voltage drop for cables. The draft is not final, so the current KS 662 still applies.
KEBS draft, Part 5: https://www.kebs.org/wp-content/uploads/2026/03/DKS-662-5-2026-PRD.pdf

## What we use
Cable: PVC insulated copper, installed in conduit on a wall (BS 7671 Reference Method B), 70 degC conductor, 30 degC ambient.

| mm2 | amps, single-phase | amps, three-phase | mV/A/m single-phase | mV/A/m three-phase |
|---|---|---|---|---|
| 1.5 | 16 | 14 | 29 | 25 |
| 2.5 | 22 | 19 | 18 | 15 |
| 4 | 30 | 26 | 11 | 9.5 |
| 6 | 38 | 33 | 7.3 | 6.4 |
| 10 | 51 | 44 | 4.4 | 3.8 |
| 16 | 68 | 60 | 2.8 | 2.4 |
| 25 | 90 | 79 | 1.8 | 1.6 |
| 35 | 111 | 97 | 1.3 | 1.15 |

## How each column was checked
- **Voltage drop, 1.5 to 16 mm2** (29, 18, 11, 7.3, 4.4, 2.8) matches Eland Cables' reproduction of BS 7671 Tables 4D2A/4D2B and Malta's government electrician exam paper (July 2025).
  https://elandcables.com/media/ek1mri4h/table-4d2a-and-4d2b.pdf
  https://myexams.gov.mt/wp-content/uploads/2025/11/Licence-A-Pr2_03-July-2025-Question-Paper.pdf
- **Voltage drop, three-phase, 1.5 to 16 mm2** (25, 15, 9.5, 6.4, 3.8, 2.4) matches the same Eland table.
- **Voltage drop, 25 and 35 mm2**: the published figures are 1.75 and 1.25, printed rounded up as 1.8 and 1.3 in the Malta paper. We use the rounded-up numbers. Three-phase values for these two sizes are our own, set slightly above 0.866 times the single-phase value.
- **Current ratings**: the published single-core Method B ratings are 17.5, 24, 32, 41, 57, 76, 101 and 125 A for 1.5 to 35 mm2 (single-phase), and 15.5, 21, 28, 36, 50, 68, 89 and 110 A (three-phase). Source: Malta's government exam papers (Licence B Pr1, July 2025), and the 2024 papers, which reproduce BS 7671 Table 4D1A.
  https://myexams.gov.mt/wp-content/uploads/2025/11/Licence-B-Pr1-02_July-2025-Question-Paper.pdf
  Twin-and-earth and multicore cables rate a little lower than single-core. A cable-maker catalogue lists multicore Method B ratings of about 16.5, 22, 30, 38, 51 and 68 A for 1.5 to 16 mm2. We use values at or below both sets. For 25 and 35 mm2 and for all three-phase values we scaled the single-core figures by the same ratio (about 0.89). That scaling is ours, so it is the part an engineer should check first.
- **Ambient temperature**: the app multiplies every rating by 0.87, the BS 7671 correction factor for 40 degC. The factors are 0.94 at 35 degC and 0.87 at 40 degC. Kenyan roof spaces and the coast can reach 40 degC.
- **Voltage drop limits**: 3% for lighting and 5% for other circuits on a supply from the public network (BS 7671 Appendix 12).

## What is not covered
Grouped cables, cables buried or in thermal insulation, aluminium cable, cable longer than the voltage-drop limit allows, and motor starting currents. For those, and for any real installation, the licensed contractor designs to KS 662.

Tests that guard this table: `node tests/qa.js`.
