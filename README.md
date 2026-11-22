# Amplifier bench projects

This repository collects small audio amplifier circuits, SPICE simulations, and bench build guides. The first hardware build is a 5 V mono amplifier with an LM358P driving a 2N2222/2N2907-family push-pull output stage. It has a board-mounted volume control and an eight-pin interface shared with a wired PAM8403-style carrier. The mono build uses the left channel. The harness provides separate speaker returns for a future stereo board.

## Start with the 2N2222 amplifier

The [build guide](circuits/2n2222/index.html) includes the parts list, breadboard layout, bench test steps, and both sides of the single-sided through-hole PCB. Open it directly in a browser or serve it from the repository root.

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory circuits/2n2222
```

Open [http://localhost:8765/](http://localhost:8765/). Start with the 8.2 Ω dummy load, then repeat the bench checks after soldering. The PCB has passed KiCad design rule checks. The build guide gives simulated reference values for the physical tests.

- [KiCad PCB](circuits/2n2222/push-pull.kicad_pcb)
- [SPICE model](circuits/2n2222/push-pull.cir), runnable with `ngspice -b circuits/2n2222/push-pull.cir`

## Documentation and reference designs

- [Experiment plan](docs/plan.md) for comparing transistor pairs, op-amp drivers, and integrated amplifiers.
- [Research notes](docs/research.txt) and [follow-up notes](docs/research2.txt) for the design background.
- [Netlist notes](net/NOTES.txt) and [amplifier choices](net/CHOICES.txt) for model assumptions and circuit options.
- [Parts lists](bom/README.txt) and [simulation comparison](reports/index.html).
- [LM386 reference build](circuits/lm386-simple/README.txt) and [tone-control tool](tools/tone-control/README.txt).
- [Change history](CHANGES.md).

## Copyright and license

Copyright (c) 2026 Michael A Wright. See [COPYRIGHT](COPYRIGHT).

The project is licensed under the [MIT License](LICENSE).
