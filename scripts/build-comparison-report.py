#!/usr/bin/env python3
"""Run ngspice comparisons and build an offline HTML/printable PDF report.
Requires matplotlib and numpy (the comparison runner needs only Python/ngspice).
"""
import csv
import html
import io
import os
import tempfile
from pathlib import Path
import subprocess
import sys
import numpy as np
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "amps-matplotlib"))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'reports'
OUT.mkdir(exist_ok=True)
cases = [
 ('Small signal: original resistor choices', 'as-proposed', .05,
  'At 50 mV peak input, the target output is 0.55 V peak. Negative feedback largely hides the modeled transistor differences. Overlapping traces are a result, not a missing curve.'),
 ('Moderate signal: common resistor values', 'common', .15,
  'With 3.3 kΩ bias resistors and 0.47 Ω emitter resistors in every stage, compare when each modeled circuit departs from its gain-11 target. Common resistors reduce one confound, but do not equalize quiescent current or optimize each transistor pair.'),
 ('High signal: common resistor values', 'common', .30,
  'The requested 3.3 V peak output drives the approximation into saturation. These runs show abrupt switching and hysteresis, not just normal sine-wave peak clipping. The generic op-amp can accumulate internal pole error during saturation and recover unrealistically; these severe shapes must not be treated as predicted hardware waveforms. Base-drive and transistor parameters also affect where saturation begins.'),
 ('High signal: original resistor choices', 'as-proposed', .30,
  'This compares the three proposed circuits as complete designs: A/B have 10 kΩ bias resistors and C has 3.3 kΩ; emitter resistors are 0.47/0.68/0.47 Ω. Differences cannot be attributed to transistor type alone.'),
]
colors = ['#1765b0', '#d16a12', '#168454']
names = ['2N2222 / 2N2907', 'BC337 / BC327', 'BD139 / BD140']
sections = []
plt.rcParams.update({'font.size': 10, 'axes.spines.top':False, 'axes.spines.right':False})
with PdfPages(OUT/'transistor-comparison.pdf') as pdf:
 for index,(title,bias,amplitude,comment) in enumerate(cases,1):
  result=subprocess.run([sys.executable,str(ROOT/'scripts/compare-transistor-pairs.py'),
                         '--bias',bias,'--input',str(amplitude)],cwd=ROOT,text=True,capture_output=True,check=True)
  run=Path(next(l.removeprefix('Results: ') for l in result.stdout.splitlines() if l.startswith('Results: ')))
  log=(run/'simulation.log').read_text()
  if 'Error:' in log or 'aborted' in log.lower():
   raise RuntimeError(log[:3000])
  with (run/'waveforms.csv').open() as f:
   rows=list(csv.reader(f))[1:]
  data=np.asarray(rows,dtype=float)
  assert data.shape[1]==5 and np.all(np.isfinite(data))
  t=data[:,0]; vin=data[:,1]; outputs=data[:,2:]
  # Endpoints are interpolated to make cycle-based RMS independent of adaptive stepping.
  ts=np.linspace(t[0],t[-1],5000,endpoint=False)
  vs=np.column_stack([np.interp(ts,t,data[:,j]) for j in range(1,5)])
  selected=t>=t[-1]-.003
  x=(t[selected]-(t[-1]-.003))*1000
  fig,axes=plt.subplots(3,1,figsize=(11,11),layout='constrained')
  fig.suptitle(f'{title}\n1 kHz · input {amplitude:g} V peak · ±6 V · 8 Ω · generic op-amp model',fontsize=14)
  axes[0].plot(x,11*vin[selected],color='#333333',ls='--',lw=1.5,label='Input × 11 (target)',zorder=5)
  table=[]
  for j,name in enumerate(names):
   y=outputs[:,j]
   axes[0].plot(x,y[selected],color=colors[j],lw=1.3,label=name)
   axes[1].plot(x,(y-11*vin)[selected]*1000,color=colors[j],label=name)
   axes[2].plot(vin[selected]*1000,y[selected],color=colors[j],label=name)
   yy=vs[:,j+1]
   matrix=np.column_stack([np.ones(len(ts)),np.sin(2*np.pi*1000*ts),np.cos(2*np.pi*1000*ts)])
   fit=np.linalg.lstsq(matrix,yy,rcond=None)[0]
   gain=np.hypot(fit[1],fit[2])/amplitude
   rms=np.sqrt(np.mean(yy**2)); residual=np.sqrt(np.mean((yy-11*vs[:,0])**2))*1000
   table.append(f'<tr><th>{html.escape(name)}</th><td>{np.ptp(yy):.4f}</td><td>{rms:.4f}</td><td>{gain:.3f}</td><td>{residual:.3f}</td></tr>')
  axes[0].set(ylabel='Output / target (V)',xlabel='Time within last 3 ms (ms)')
  axes[1].set(ylabel='Output − 11 × input (mV)',xlabel='Time within last 3 ms (ms)')
  axes[2].plot(vin[selected]*1000,11*vin[selected],color='#333',ls='--',label='Ideal gain 11')
  axes[2].set(ylabel='Output (V)',xlabel='Input (mV)',title='Transfer curves: diagonal = linear gain; plateaus/loops = saturation and recovery effects')
  for ax in axes:
   ax.grid(alpha=.22);ax.legend(fontsize=8,loc='best')
  buf=io.StringIO();fig.savefig(buf,format='svg');svg=buf.getvalue();svg=svg[svg.index('<svg'):]
  fig.savefig(OUT/f'case-{index}.svg')
  fig.savefig(OUT/f'case-{index}.png', dpi=110)
  fig.text(.5,.001,'Educational model results; not measured hardware performance or a validated audio-quality ranking.',ha='center',fontsize=8)
  pdf.savefig(fig);plt.close(fig)
  copied=OUT/f'case-{index}-waveforms.csv';copied.write_bytes((run/'waveforms.csv').read_bytes())
  (OUT/f'case-{index}.net').write_bytes((run/'comparison.net').read_bytes())
  sections.append(f'''<section><h2>{index}. {html.escape(title)}</h2><p>{html.escape(comment)}</p>{svg}
<table><thead><tr><th>Pair</th><th>Output Vpp</th><th>Output Vrms</th><th>Fundamental gain (V/V)</th><th>Residual RMS (mV)</th></tr></thead><tbody>{''.join(table)}</tbody></table>
<p class="small">Metrics use the final ten cycles after 200 ms settling. Residual includes gain error, phase shift and nonlinear error; it is not THD. RMS includes DC.</p>
<p><a href="case-{index}-waveforms.csv">Waveform CSV</a> · <a href="case-{index}.net">Exact runnable deck</a> · <a href="case-{index}.svg">SVG figure</a></p></section>''')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Three transistor-pair amplifier simulations</title>
<style>body{font:17px/1.55 system-ui,sans-serif;max-width:1120px;margin:36px auto;padding:0 24px;color:#202c38;background:#f7f8fa}h1{line-height:1.15}h2{line-height:1.25}section,.intro{background:white;padding:24px;margin:24px 0;border:1px solid #dce1e5;border-radius:10px}svg{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;text-align:left;border-bottom:1px solid #dde3e8}.notice{border-left:5px solid #cf7a12;padding:12px 18px;background:#fff2dc}.small{font-size:14px;color:#485566}a{color:#125fa7}button{padding:10px 20px;font-size:16px;cursor:pointer}code,pre{background:#edf1f5;padding:3px}pre{padding:14px;overflow:auto} @media print{body{background:white;max-width:none;margin:0;padding:0;font-size:11pt}section,.intro{border:0;padding:0;break-before:page}section{break-inside:avoid}button,.downloads{display:none}svg{max-height:200mm}a{color:inherit}.intro{break-before:auto}} </style>
<h1>Three transistor-pair amplifier simulations</h1>
<p>Shared sine-wave input · three simultaneous outputs · ngspice 47</p>
<button onclick="window.print()">Print report / Save PDF</button>
<p class="downloads"><a href="transistor-comparison.pdf">Download plot PDF (4 pages)</a> · <a href="plan.md">Month-long project plan</a> · <a href="parts/">Project parts lists</a></p>
<div class="intro"><h2>What these plots represent</h2>
<p>A = 2N2222/2N2907; B = BC337/BC327; C = BD139/BD140. These are the first three amplifier circuits from the research discussion, with a DC input return, base stopper resistors, and output decoupling/stabilization added consistently. They are separate circuits fed by the same simulated signal source.</p>
<p class="notice"><strong>This is an educational circuit comparison, not a reliable transistor-quality ranking.</strong> The missing LM741 model is replaced by the same generic one-pole model in all three branches. It has no slew limiting, output-current limit, input bias, offset, or noise. The BC and BD transistor models supplied in the discussion are simplified and unvalidated. None of these plots is a measurement of your parts.</p>
<h2>What to look for</h2><p>At low level, all three outputs should almost overlap because global feedback sets gain near 11. Increase amplitude to reveal modeled compression and clipping. A rounded or flat peak shows loss of proportional gain. Transfer curves show this as a bend away from a straight diagonal. Difference plots magnify departures from the gain-11 target.</p>
<p>At high input, the square-like waveforms and wide transfer loops expose saturation-recovery limitations of the generic op-amp model. Treat those figures as a reason to improve the model and investigate the circuit, not as expected bench traces.</p><p>The discussion predicted BD139/BD140 would always be cleaner and swing farther. These models do not establish that claim. BD devices can be useful for current handling and heatsinking, but lower current gain can demand more base drive. Available bias current and the op-amp drive capability matter. There is no predetermined winner here.</p>
<p>In real builds, thermal behavior, bias tracking, device spread, layout and feedback stability can change the result. A 741 can introduce high-frequency slew distortion that this model cannot show. Compare multiple actual samples before treating transistor type as the cause of a difference.</p></div>
'''+''.join(sections)+'''
<section><h2>Repeat the experiment</h2><pre>python scripts/compare-transistor-pairs.py --gui
python scripts/compare-transistor-pairs.py --bias common --input 0.15 --gui
python scripts/compare-transistor-pairs.py --bias common --input 0.30 --gui</pre>
<p>GUI mode leaves ngspice open; enter <code>quit</code> when finished. Without <code>--gui</code>, each run saves a deck, log and CSV under results/. The report builder requires NumPy and Matplotlib:</p>
<pre>/disk1/tmp/amps-report-venv/bin/python scripts/build-comparison-report.py</pre>
<p>Next: replace the generic op-amp with a suitable vendor model, check idle currents and transistor dissipation, then reproduce the same tests with three independent dummy loads and a four-channel scope. See the project plan.</p>
<h2>References</h2><p><a href="https://www.ti.com/lit/ds/symlink/lm741.pdf">TI LM741 datasheet</a> · <a href="https://ngspice.sourceforge.io/docs.html">ngspice documentation</a>. Original circuit/model text: docs/research.txt in this repository.</p></section></html>'''
(OUT/'index.html').write_text(page)
(OUT/'plan.md').write_bytes((ROOT/'docs/plan.md').read_bytes())
print(OUT/'index.html')
