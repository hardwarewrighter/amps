#!/usr/bin/env python3
"""Run the three transistor pairs in ngspice; export settled waveforms as CSV."""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=float, default=0.05, help='input peak volts (default 0.05)')
parser.add_argument('--frequency', type=float, default=1000, help='sine frequency Hz')
parser.add_argument('--bias', choices=['as-proposed', 'common'], default='as-proposed')
parser.add_argument('--gui', action='store_true', help='open ngspice graphs and leave interactive prompt')
args = parser.parse_args()
if args.input <= 0 or args.frequency <= 0:
    parser.error('input and frequency must be positive')
if not shutil.which('ngspice'):
    parser.error('ngspice is missing; install it with pacman')
root = Path(__file__).resolve().parent.parent
# All names generated here are safe ngspice command tokens; use cwd for output paths.
out = root / 'results' / ('pairs-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
out.mkdir(parents=True)
deck = (root / 'net/transistor-pairs-comparison.net').read_text()
deck = deck.replace('V_INPUT=0.05 FREQ=1000', f'V_INPUT={args.input:.12g} FREQ={args.frequency:.12g}')
if args.bias == 'common':
    deck = deck.replace('RB_A=10k RB_B=10k RB_C=3.3k RE_A=0.47 RE_B=0.68 RE_C=0.47',
                        'RB_A=3.3k RB_B=3.3k RB_C=3.3k RE_A=0.47 RE_B=0.47 RE_C=0.47')
# Allow at least 200 ms settling; export the final ten whole cycles.
period = 1 / args.frequency
start = max(0.2, 20 * period)
stop = start + 10 * period
step = min(2e-6, period / 500)
commands = f'''
.control
set noaskquit
set wr_singlescale
set wr_vecnames
tran {step:.12g} {stop:.12g} {start:.12g} {step:.12g}
wrdata waveforms.txt v(Input) v(Out_A) v(Out_B) v(Out_C)
meas tran input_rms RMS v(Input) from={start:.12g} to={stop:.12g}
meas tran a_rms RMS v(Out_A) from={start:.12g} to={stop:.12g}
meas tran b_rms RMS v(Out_B) from={start:.12g} to={stop:.12g}
meas tran c_rms RMS v(Out_C) from={start:.12g} to={stop:.12g}
'''
if args.gui:
    commands += '''plot v(Input) v(Out_A) v(Out_B) v(Out_C)
plot v(Out_A) v(Out_B) v(Out_C) 11*v(Input)
plot v(Out_A)-11*v(Input) v(Out_B)-11*v(Input) v(Out_C)-11*v(Input)
'''
else:
    commands += 'quit\n'
commands += '.endc\n.END\n'
deck = deck[:deck.rindex('.END')] + commands
(out / 'comparison.net').write_text(deck)
(out / 'settings.txt').write_text(f'{vars(args)}\nA=2N2222/2N2907; B=BC337/BC327; C=BD139/BD140\n'
                                'Generic op-amp model; unvalidated transistor models.\n')
print(f'Results: {out}', flush=True)
command = ['ngspice', 'comparison.net'] if args.gui else ['ngspice', '-b', '-o', 'simulation.log', 'comparison.net']
subprocess.run(command, cwd=out, check=True)
raw = out / 'waveforms.txt'
if not raw.exists():
    raise SystemExit('No waveform export: inspect simulation.log or terminal errors.')
with raw.open() as source, (out / 'waveforms.csv').open('w', newline='') as target:
    writer = csv.writer(target)
    writer.writerow(['time_s', 'input_V', '2n2222_2n2907_V', 'bc337_bc327_V', 'bd139_bd140_V'])
    for line in source:
        cols = line.split()
        if len(cols) == 5:
            try:
                values = [float(value) for value in cols]
            except ValueError:
                continue
            writer.writerow(values)
print('CSV saved. Model results are illustrative; validate on the bench.')
