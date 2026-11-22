#!/usr/bin/env python3
"""Create draft circuit BOM CSVs and an offline HTML parts-list index."""
import csv
from collections import defaultdict
import html
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'bom'
WEB=ROOT/'reports/parts'
OUT.mkdir(exist_ok=True);WEB.mkdir(parents=True,exist_ok=True)
fields=['quantity','references','part','value','category','notes']
projects={'lm386n-simple-amp':'P00','lm386n-amp':'P00', '2n2222-amp':'P01','bc337-amp':'P02','bd139-amp':'P03','transistor-pairs-comparison':'P04','ne5532-bd139-amp':'P05','jrc4558-bd139-amp':'P06','lm358-bd139-amp':'P07','lm324-bd139-amp':'P08','741-bd139-amp':'P09','battery-swap-soft-mute':'P12','lm386-simple-kicad':'P00 / PCB learning project'}
sections=[]

def save(name,rows,source):
    rows=sorted(rows,key=lambda r:(r['category'],r['part'],r['value']))
    path=OUT/(name+'.csv')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)
    shutil.copyfile(path,WEB/path.name)
    header=''.join('<th>'+html.escape(k.replace('_',' ').title())+'</th>' for k in fields)
    cells=''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in fields)+'</tr>' for r in rows)
    sections.append(f'<section><h2>{projects.get(name, "")} — {html.escape(name)}</h2><p>Source: {html.escape(source)} · <a href="{path.name}">CSV parts list</a></p><table><thead><tr>{header}</tr></thead><tbody>{cells}</tbody></table></section>')

for file in sorted((ROOT/'net').glob('*.net')):
    params=dict(re.findall(r'(\w+)\s*=\s*([^\s]+)', '\n'.join(l for l in file.read_text().splitlines() if l.upper().startswith('.PARAM')),re.I))
    def resolve(value):
        return re.sub(r'\{(\w+)\}',lambda m:params.get(m[1],m[0]),value)
    grouped=defaultdict(list)
    for line in file.read_text().splitlines():
        if line.upper().startswith('.SUBCKT'):break
        tokens=line.split()
        if not tokens or tokens[0][0] in '*.+':continue
        ref=tokens[0];kind=ref[0].upper()
        category='Circuit part';notes='Draft from simulation; verify before building.'
        if kind=='R':
            value=resolve(tokens[3]);part='Resistor'
            if 'LOAD' in ref.upper() or ref.upper()=='R_L' or ref.upper()=='R_SPEAKER':
                category='External load';notes='Speaker or noninductive dummy load; choose power rating for the measured output.'
            elif value in ['0','0V']:
                category='Simulation connection';notes='Ideal connection, not a resistor to buy.'
            elif ref.upper().startswith(('R_E','R_EP','R_EN')):
                notes='Emitter resistor; evaluate dissipation and required wattage (start with 0.5 W for the low-power experiments).'
            else:
                notes='Resistance in ohms; wattage and tolerance require design review.'
        elif kind=='C':
            value=resolve(tokens[3]);part='Capacitor';notes='Check polarity/type and voltage rating against the schematic and supply.'
        elif kind in ['D','Q','J']:
            part={'D':'Diode','Q':'Bipolar transistor','J':'JFET'}[kind]
            value=tokens[-1]
            if value=='J2N5485':value='2N5485'
            notes='Verify actual package pinout; model name alone does not specify the package.'
        elif kind=='X':
            value='LM386N' if file.stem.startswith('lm386') else ('NE5532' if file.stem.startswith('ne5532') else 'JRC4558 / NJM4558' if file.stem.startswith('jrc4558') else 'LM358 / LM358P' if file.stem.startswith('lm358') else 'LM324' if file.stem.startswith('lm324') else 'LM741CN / UA741')
            part='Amplifier IC channel';notes='Quantity counts used channels, not necessarily IC packages. Single 741: 1/channel; duals: up to 2/package; LM324: up to 4/package. Terminate unused channels.'
            if value=='LM386N':notes='One DIP-8 IC; verify -1/-3/-4 suffix. Uses an approximate simulation model.'
        elif kind in ['V','S']:
            part='Voltage source' if kind=='V' else 'Ideal controlled switch'
            value=' '.join(tokens[3:]) if kind=='V' else tokens[-1]
            category='Simulation / test fixture'
            notes='Not a physical BOM item. Supply, generator, sensing connection or control abstraction.'
            if kind=='S':notes='Conceptual contact only: relay/MOSFET, driver and controller implementation still undefined.'
        else:continue
        grouped[part,value,category,notes].append(ref)
    rows=[dict(quantity=len(refs),references='; '.join(refs),part=p,value=v,category=c,notes=n) for (p,v,c,n),refs in grouped.items()]
    save(file.stem,rows,str(file.relative_to(ROOT)))

components=json.loads((ROOT/'circuits/lm386-simple/components.json').read_text())['parts']
rows=[]
for c in components:
    if c['ref'].startswith('#'):continue
    kind=c['ref'][0]
    part={'U':'Amplifier IC','C':'Capacitor','R':'Resistor','J':'2-pin connector'}[kind]
    notes='Provisional footprint: '+c['footprint']
    if c['ref'] in ['C3','C4']:notes+='; polarized electrolytic, at least 10 V; verify dimensions.'
    rows.append(dict(quantity=1,references=c['ref'],part=part,value=c['value'],category='Circuit part',notes=notes))
rows.extend([dict(quantity=1,references='External speaker',part='Speaker / dummy load',value='8 ohms',category='External load',notes='Not a PCB component; suitable power rating required.'),dict(quantity=1,references='Power',part='Regulated supply',value='+6 V single supply',category='Test fixture',notes='Current-limited supply or suitable battery source; not an IC component.')])
save('lm386-simple-kicad',rows,'circuits/lm386-simple/components.json')

page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amplifier project parts lists</title>
<style>body{font:16px/1.5 system-ui;max-width:1300px;margin:30px auto;padding:0 20px;color:#223}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;vertical-align:top;padding:8px;border:1px solid #ccd}section{margin:36px 0}button{padding:10px} @media print{button{display:none}section{break-before:page}table{font-size:9pt}tr{break-inside:avoid}}</style>
<h1>Parts lists by amplifier project</h1><button onclick="print()">Print / Save PDF</button>
<p>Use the <strong>LM386 KiCad list</strong> for the generated graphical project. Other lists are draft extractions of the current simulation circuits. Their model limitations and known circuit issues still apply. Simulation sources and external test loads are separated from circuit parts.</p>
<p><strong>Do not add all CSV quantities together:</strong> many files are alternative versions of the same project. Op-amp channel quantities differ from package quantities. Wiring, sockets, breadboards, connectors absent from the netlists, decoupling/layout improvements and heatsinks must be considered separately.</p>
<p>For the first three-way fixture: three independent 8-ohm dummy loads, shared generator, four scope probes, a suitable split supply, wiring and temperature/current measurements. Use measured resistor dissipation and device ratings to select power ratings. IC sockets are optional. The transistor-pairs-comparison list includes all three channels, so do not also add P01/P02/P03.</p>
<h2>Projects without a final parts list</h2><ul><li>P10 TDA2822: exact device/package and circuit still need selection. LM386 alternatives are listed below.</li><li>P11 TDA2030: circuit, supply, heatsink and load ratings still need selection.</li><li>P12 battery switching: conceptual netlist only; not a complete hardware purchasing list.</li><li>P13 final PCB: depends on the amplifier selected after evaluation. The current LM386 PCB is an unrouted learning board.</li></ul>
'''+''.join(sections)+'</html>'
(WEB/'index.html').write_text(page)
(OUT/'README.txt').write_text('''View reports/parts/index.html for printable lists and project status.
CSV files in this directory are generated by scripts/build-parts-lists.py.
The LM386 KiCad list follows the graphical project's 220uF / 47nF values;
the older netlists have 250uF / 50nF instead. These are alternatives.
Netlist-based lists are drafts, not hardware-validated purchasing lists.
Known source design/model issues still apply. Simulation items are identified.
Do not sum mutually alternative project lists. See the HTML for pending projects.
''')
print(f'Created {len(sections)} CSV lists; {WEB}/index.html')
