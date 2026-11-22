Open lm386-simple.kicad_sch in KiCad Schematic Editor, or open
lm386-simple.kicad_pro in the KiCad project manager.

All ten physical components are placed and wired. KiCad 10.0.7 ERC:
zero errors, zero warnings. Exported pin connectivity was checked against
the intended circuit, including the positive side of C4 facing U1 pin 5.

lm386-simple.pdf is the printable schematic.
lm386-simple.kicad_pcb is a placed, UNROUTED learning board with footprints
and net connections. It is not ready for fabrication. Footprints are
provisional; check sizes against your actual capacitors/connectors first.
Use Update PCB from Schematic (F8) after editing the schematic.

This drawing uses 220uF output coupling and 47nF in the RC network, standard
values replacing 250uF/50nF in the earlier netlist. C3 and C4 are polarized.
Pins 1/7/8 are intentionally open. Supply is single +6 V; load is an external
8-ohm speaker at J3. This has no volume control; start with a small input.

The graphical project is for drawing/PCB exploration. Simulation sources
and a KiCad simulation model have not been attached to its symbols.
For the corresponding standalone ngspice example, run:
  ngspice circuits/lm386-simple/lm386-simple.cir
That uses the same approximate educational model as the earlier LM386 deck;
it does not validate power, distortion, stability or thermal performance.

Project-local library tables refer to the installed Arch KiCad libraries.
Embedded symbols allow the schematic to display without external symbols.
