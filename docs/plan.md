# One month of amplifier comparisons

Start with the three transistor-pair amplifiers in `research.txt`. Simulate each circuit before breadboarding, compare three outputs against one common input, and use the evidence to choose a PCB project. The LM386 is a short tools/setup exercise; it must not displace the first three amplifier experiments.

This is a proposed 30-day work plan. Schematics, validated device models, breadboards and PCBs listed below are future deliverables unless explicitly marked present. KiCad 10.0.7 and ngspice 47 are installed. Existing `.net` files are simulation decks, not graphical schematics or PCB layouts.

## Tools and files: what to open first

| Task | Tool | Files / action |
|---|---|---|
| Read and edit circuit connections now | Existing text editor | `net/*.net`; start with `lm386n-simple-amp.net`, then `transistor-pairs-comparison.net` |
| Run text circuits and inspect waveforms now | ngspice, launched in a terminal | `ngspice net/lm386n-simple-amp.net` |
| Compare the first three amplifiers now | Python runner + ngspice | `python scripts/compare-transistor-pairs.py --gui` |
| View and print comparison plots now | Laptop web browser | `reports/index.html`, served on `0.0.0.0`; browser Print / Save as PDF |
| View a printable plot artifact | Browser or PDF viewer | `reports/transistor-comparison.pdf` |
| Draw, view and edit actual schematics soon | KiCad Schematic Editor | Create `.kicad_pro` and `.kicad_sch` per project; these files do not exist yet |
| Simulate graphical schematics | KiCad simulator, using ngspice | Assign SPICE models and verify symbol/model pin mapping |
| Print a circuit drawing | KiCad PDF plotting, then browser/PDF viewer | Export each schematic to PDF; print a dated revision with values and pin labels |
| Design PCB later | KiCad PCB Editor | `.kicad_pcb`, updated from the validated schematic |
| Check manufacturing exports later | KiCad Gerber Viewer | Gerber layers and Excellon drill files |
| Rebuild report figures | Python + NumPy + Matplotlib | `scripts/build-comparison-report.py`; current environment: `/disk1/tmp/amps-report-venv/bin/python` |

Commands for a new Arch setup, or to fill gaps without reinstalling existing packages:

```bash
sudo pacman -Syu --needed ngspice kicad kicad-library
# Optional component bodies for the PCB 3D view:
sudo pacman -S --needed kicad-library-3d
# Optional system-wide report plotting dependencies:
sudo pacman -S --needed python-numpy python-matplotlib
```

No extra PCB program is required. Use the existing editor, browser and printer setup. KiCad can export PDFs without a working local printer; the laptop can print them. Install/configure printer support only if direct printing from this host is needed.

### First ngspice session

From the repository root:

```bash
ngspice net/lm386n-simple-amp.net
```

At the ngspice prompt:

```text
tran 2u 200m
plot v(speaker) v(audio_in) xlimit 180m 185m
plot v(speaker) 20*v(audio_in) xlimit 180m 185m
plot v(speaker)-20*v(audio_in) xlimit 180m 185m
quit
```

The scaled input and output may overlap. The residual magnifies gain/phase errors and is not THD. This circuit is an LM386, with no external transistor pair. Its output coupling capacitor causes signal-startup settling; examine settled cycles.

### File conversion and virtual construction

A SPICE `.net` does not contain symbol positions or drawing geometry. Do not expect opening it in KiCad to produce a readable schematic. Reconstruct each circuit in KiCad, label nets to match the deck, check connections, assign models, and export a fresh SPICE deck. Use a project-local model library with source URL, version, license and pin mapping recorded. Keep the original research extractions unchanged.

Once the schematic exists, treat it as the maintained design source and regenerate simulation exports from it. Verify exported connectivity against the original deck; do not hand-edit two independent versions indefinitely. Keep both the actual package pin numbers and the SPICE terminal order documented.

## Projects, in priority order

| ID | Circuit / experiment | Present starting files | Intended result |
|---|---|---|---|
| P00 | LM386 tool check, gain 20, +6 V | `lm386n-simple-amp.net`, `lm386n-amp.net` | One quick simulation and optional simple build to learn the workflow |
| P01 | 2N2222 / 2N2907 amplifier | `2n2222-amp.net` | First three-way benchmark channel A |
| P02 | BC337 / BC327 amplifier | `bc337-amp.net` | First benchmark channel B |
| P03 | BD139 / BD140 amplifier | `bd139-amp.net` | First benchmark channel C |
| P04 | Simultaneous pair comparison | `transistor-pairs-comparison.net`, comparison script | Shared input and three independent output stages; report and repeatable bench fixture |
| P05 | NE5532 + chosen transistor pair | `ne5532-bd139-amp.net` | Audio-oriented op-amp candidate |
| P06 | JRC4558 + same pair | `jrc4558-bd139-amp.net` | Alternative using available spares |
| P07 | LM358 / LM358P + same pair | `lm358-bd139-amp.net` | General-purpose comparison candidate |
| P08 | LM324 + same pair | `lm324-bd139-amp.net` | Quad alternative, distinct package wiring |
| P09 | LM741CN / UA741 + same pair | `741-bd139-amp.net` | 741-family reference; check exact vendor/suffix |
| P10 | Integrated low-power speaker amp | LM386 decks; TDA2822 schematic/deck to create | Compare circuit families after P01–P04; confirm TDA2822 full marking and pin count first |
| P11 | TDA2030 speaker amp | Schematic/deck to create | Later higher-power experiment with suitable supply, heatsink and load |
| P12 | Battery switching and soft mute | `battery-swap-soft-mute.net` | Last priority; repair switch/control model before simulation or building |
| P13 | PCB for the selected amplifier | KiCad files to create | Reviewed manufacturing export, not an automatic board order |

LM358P and LM358 are one device family. LM741CN and UA741 are closely related choices, not four independent architectures. Dual op-amps can provide multiple channels, but sharing one IC can introduce supply/package coupling. Use available spares, record exact markings and channel assignments, and test unused-channel termination. LM324 and 741 packages are not socket replacements for a dual DIP-8 op-amp. LM386/TDA parts are speaker amplifiers with different connections.

## Simulation checkpoint before each build

1. Check the schematic against the actual device datasheet, including the transistor lead order. Correct the missing input DC return and zero-ohm driver connection in derived versions. Confirm unused op-amp channels are properly terminated.
2. Obtain appropriate vendor SPICE models where available. Check subcircuit names and terminal order. Library symbols/footprints do not guarantee a simulation model exists. If no validated model is available, mark the project exploratory and restrict conclusions accordingly.
3. Run a DC operating point: input common-mode range, near-zero split-supply output offset, idle collector currents, resistor dissipation and transistor dissipation. Reject unreasonable bias before a load test.
4. Run small-signal AC response, initially 20 Hz–100 kHz, and transient sine tests at 100 Hz, 1 kHz, 10 kHz and 20 kHz. Start below clipping, then increase input in small steps. Check supply headroom and any model warnings.
5. Inspect settling and oscillation; include load capacitance or a speaker model only after the resistive-load baseline. Step response and model-based loop analysis can expose concerns, but a clean simulated sine does not establish physical stability.
6. Save the exact circuit revision, model provenance, settings, plots and summary before breadboarding.

Current limitations: the extracted P01–P03 decks omit their LM741 model. The self-contained derived decks and combined comparison use an educational one-pole op-amp, without realistic slew limiting, output-current limits or noise. Research BC/BD transistor models are simplified. Those decks run but cannot validate claims about real distortion, thermal behavior or sound quality. Current report figures are explicitly exploratory.

## Four-channel comparison fixture

```text
Function generator signal ──┬── CH1 (actual common input)
                            ├── amplifier A input ── output A ── load A ── GND
                            ├── amplifier B input ── output B ── load B ── GND
                            └── amplifier C input ── output C ── load C ── GND
                                             CH2      CH3      CH4
                                   (probe each respective output)
```

Use CH1 for input, CH2=A, CH3=B, CH4=C. Four channels allow **three amplifiers plus input simultaneously**. Compare additional amps in later groups while retaining a reference amplifier; more simultaneous amplifiers need more acquisition channels.

- Use three separate measured, noninductive 8 Ω dummy loads, initially rated at least 5 W each for these low-power tests. Size higher-power loads from measured dissipation and derate for heating; the TDA2030 may need substantially larger ratings. Do not connect amplifier outputs together.
- All normal passive-probe grounds and the generator return connect to the common circuit 0 V. On split supplies this is the midpoint, never the negative rail. Standard bench scope grounds are normally common and earth-referenced. Verify the PSU grounding arrangement before connecting instruments. Keep the oscilloscope earth connected. Bridge-output measurements require an appropriate differential setup; do not attach ground clips to active outputs.
- Use compensated 10× probes, matched scope settings and high-impedance inputs. Do not select 50 Ω scope termination for the amplifier outputs. Check whether the generator amplitude display assumes a 50 Ω load; trust CH1's measured voltage at the actual input node.
- Use short wiring, local rail decoupling, and separate output-current returns to a common supply point. Monitor rail sag: supply interaction can imitate amplifier differences. First characterize each amplifier alone with current limiting, then connect all three.
- Start with a 1 kHz sine around 20–50 mV peak, confirming units on CH1. Use DC coupling first to check offset. Then adjust display scales to compare waveform shape; trigger from CH1. Preserve actual gain measurements rather than hiding differences with arbitrary vertical scaling.
- Keep the input and loads the same within a run. Never increase a shared input beyond a weaker amplifier's safe limits solely to stress another one. Characterize higher safe levels separately if needed.

## Measurement protocol and records

Perform two distinct comparisons of P01–P03:

1. **As proposed:** retain each circuit's original bias/emitter resistor values after correcting connectivity errors. This compares complete designs, with resistor choices as confounding variables.
2. **Controlled comparison:** use the same op-amp type, rails, gain, load and layout approach. First simulate common resistor values, then evaluate appropriate bias for each pair; equal resistor values do not guarantee equal idle current. Record all changes. If selecting bias for equal idle current, identify that as a separate test rather than silently tuning one candidate.

At 100 Hz, 1 kHz, 10 kHz and 20 kHz, record gain and phase at a low common output level, distortion indicators at equal output level, and the onset of clipping as input increases. Use a repeatable clipping criterion (for example 1% gain compression relative to the low-level fundamental gain), distinct from visual clipping. Record the input where the criterion is met; do not equate this criterion with 1% THD.

For a clean sine into a resistor, `P = Vrms² / R`; once clipped, use waveform RMS and report distortion separately. Also record DC offset, idle current, rail voltages, temperature, warm-up time and measured load resistance. Repeat with another transistor sample and swap loads/probes if an apparent advantage is small.

Scope FFT is a supplementary harmonic comparison, not automatically a precision THD instrument. Use the same sampling, window, record length, number of settled cycles and bandwidth for all channels. Check the generator's own distortion and scope floor. Save raw waveform CSVs and screenshots. Residual `output − gain × input` includes phase and gain errors; align and normalize appropriately before interpreting a residual as nonlinear error. Lack of visible distortion does not prove audibly identical performance.

Suggested run record columns:

```text
run_id, revision, models_or_hardware, pair, opamp_marking, channel,
rails_V, input_Hz, input_Vrms, output_Vrms, gain, phase_deg,
load_ohms, idle_mA, offset_mV, clipping_criterion, temperature_C,
warmup_minutes, scope_settings, notes
```

Store each experiment under a dated results folder with the deck or schematic revision and settings. Existing comparison runner outputs already include a runnable deck, log, settings and CSV.

## Month schedule

| Days | Work | Completion evidence |
|---|---|---|
| 1–2 | Verify installed tools, try P00 briefly, inventory transistor/op-amp quantities, identify scope/generator/PSU limits; draw P01–P03 in KiCad and attach available models | Printed schematics, parts inventory and model-gap list |
| 3–4 | P01–P04 DC/AC/transient simulations; reproduce low-level overlap and amplitude-dependent compression; resolve bias problems | Saved virtual comparison and clearly stated model limits |
| 5–7 | Bring up P01–P03 individually, then compare all three simultaneously at 1 kHz and the four test frequencies | First bench report, before other circuit experiments |
| 8–10 | Repeat transistor comparison using common conditions and documented bias choices; include warm-up and second samples | Pair conclusions with error/confound notes |
| 11–14 | Hold transistor pair fixed; compare NE5532, JRC4558 and whichever of 741/LM358/LM324 has most spares, then rotate remaining choices | At least one three-op-amp comparison with a retained reference |
| 15–17 | Simulate, then build LM386 baseline if not already built; compare against two retained discrete references at equal output power | Circuit-family comparison, with gain differences accounted for |
| 18–21 | TDA2822 after package identification; TDA2030 only with suitable power/heatsink/load. If those are unavailable, repeat or improve earlier measurements | One additional validated circuit, or stronger earlier evidence |
| 22–24 | Select one design from measurements; finish schematic, BOM, exact footprints and connectors; choose simple repeatable test-point access | Frozen schematic revision and footprint checks against actual parts |
| 25–27 | Lay out a two-layer board; short feedback path and local decoupling, deliberate high-current returns, thermal clearance; run ERC/DRC | Reviewed PCB with resolved or justified findings |
| 28–30 | Export, inspect and archive manufacturing package; optional battery/mute simulation only after amplifier priorities | Gerbers + drills + BOM + assembly drawing + test procedure |

Assume one focused bench session per day with catch-up time on the last day of each week. Model or component gaps should reduce optional projects rather than delay the first three-way bench comparison indefinitely. Virtual tests inform the build; they cannot replace missing manufacturer characterization.

## Reproducible comparison and report

```bash
# Plots and interactive ngspice prompt:
python scripts/compare-transistor-pairs.py --gui
# Common resistor values, with a larger sine input:
python scripts/compare-transistor-pairs.py --bias common --input 0.15 --gui
python scripts/compare-transistor-pairs.py --bias common --input 0.30 --gui
# Generate offline HTML, SVGs, CSV links and a plot PDF:
/disk1/tmp/amps-report-venv/bin/python scripts/build-comparison-report.py
# Serve only the report directory to the LAN:
python -m http.server 8000 --bind 0.0.0.0 --directory reports
```

GUI runs save CSV after exiting ngspice with `quit`. Without `--gui`, the runner saves files and exits automatically. The report contains four 1 kHz cases: small-signal original resistors, moderate/high input common resistors, and high-input original resistors. Plot axes and tables show simulation results, not assumed device rankings. High-input runs show abrupt switching and hysteresis dominated in part by the generic op-amp saturation-recovery behavior; replace that model before making hardware waveform predictions.

## PCB export checkpoint

Use the bench-tested design and actual package variants. Verify pad numbering, board outline, mounting holes, connector polarity, heatsink/tab connections and clearances. Add labeled input/output/ground/rail test points. Run schematic electrical checks and board design checks. Export Gerber copper, solder mask, silkscreen and outline layers plus Excellon drill files; add BOM, schematic PDF and assembly/placement information as needed. Reopen the export in Gerber Viewer, checking drills and outline alignment. Archive native KiCad files and exact exports together. Board ordering and assembly are separate later actions.

## References

- [KiCad on Arch Linux](https://www.kicad.org/download/details/arch-linux/)
- [KiCad schematic editing, plotting and simulation](https://docs.kicad.org/10.0/en/eeschema/eeschema.html)
- [KiCad board design and manufacturing exports](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)
- [ngspice documentation](https://ngspice.sourceforge.io/docs.html)
- [Tektronix probe grounding and measurement guidance](https://www.tek.com/en/documents/whitepaper/abcs-probes-primer)
- Device references and current circuit limitations: `net/CHOICES.txt`, `net/NOTES.txt`, and comments in each derived deck.
