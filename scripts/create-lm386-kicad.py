#!/usr/bin/env python3
"""Generate the LM386 learning schematic from installed KiCad library symbols."""
from pathlib import Path
import json
import math
import re
import uuid

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'circuits/lm386-simple'
OUT.mkdir(parents=True,exist_ok=True)
NAME='lm386-simple'
uid=lambda: str(uuid.uuid4())
q=lambda s: json.dumps(str(s))
root_uuid=uid()

def extract(library,name):
    data=Path('/usr/share/kicad/symbols',library+'.kicad_sym').read_text()
    start=data.index('(symbol '+q(name)+'\n')
    depth=0; quoted=False; escaped=False
    for i in range(start,len(data)):
        c=data[i]
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0:
                return data[start:i+1].replace('(symbol '+q(name), '(symbol '+q(library+':'+name),1)
    raise ValueError(name)

libraries=[('Amplifier_Audio','LM386'),('Device','C'),('Device','C_Polarized'),('Device','R'),('Connector_Generic','Conn_01x02'),('power','PWR_FLAG')]
lib={f'{a}:{b}':extract(a,b) for a,b in libraries}
parts=[];items=[]

def prop(name,value,x,y,hidden=False):
    return f'(property {q(name)} {q(value)} (at {x:g} {y:g} 0) (effects (font (size 1.27 1.27))'+(' (hide yes)' if hidden else '')+'))'

def symbol(lib_id,ref,value,x,y,angle=0,footprint='',label_x=None,label_y=None):
    ident=uid(); lx=x+6.35 if label_x is None else label_x; ly=y-3.81 if label_y is None else label_y
    pins=re.findall(r'\(number "([^"]+)"',lib[lib_id])
    items.append(f'''(symbol (lib_id {q(lib_id)}) (at {x:g} {y:g} {angle}) (unit 1)
(exclude_from_sim {'yes' if ref.startswith('J') else 'no'}) (in_bom {'no' if ref.startswith('#') else 'yes'}) (on_board {'no' if ref.startswith('#') else 'yes'}) (dnp no) (uuid "{ident}")
{prop('Reference',ref,lx,ly,ref.startswith('#'))}
{prop('Value',value,lx,ly+2.54,ref.startswith('#'))}
{prop('Footprint',footprint,x,y,True)}
{''.join(f'(pin {q(pin)} (uuid "{uid()}"))' for pin in pins)}
(instances (project "{NAME}" (path "/{root_uuid}" (reference {q(ref)}) (unit 1)))))''')
    parts.append(dict(ref=ref,value=value,lib_id=lib_id,x=x,y=y,angle=angle,footprint=footprint,uuid=ident))

def wire(*pts):
    for a,b in zip(pts,pts[1:]):
        assert a!=b
        items.append(f'(wire (pts (xy {a[0]:g} {a[1]:g}) (xy {b[0]:g} {b[1]:g})) (stroke (width 0) (type default)) (uuid "{uid()}"))')

def label(name,x,y):
    items.append(f'(label {q(name)} (at {x:g} {y:g} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))')

def junction(x,y):
    items.append(f'(junction (at {x:g} {y:g}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))')

def text(s,x,y,size=1.27):
    items.append(f'(text {q(s)} (at {x:g} {y:g} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid()}"))')

def nc(x,y):
    items.append(f'(no_connect (at {x:g} {y:g}) (uuid "{uid()}"))')

DIP='Package_DIP:DIP-8_W7.62mm'
CAP='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
EL='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
CON='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
symbol('Amplifier_Audio:LM386','U1','LM386N',127,88.9,footprint=DIP,label_x=139.7,label_y=76.2)
symbol('Device:C','C1','1u',88.9,86.36,90,CAP,label_x=88.9,label_y=77.47)
symbol('Device:C','C2','100n',99.06,55.88,footprint=CAP)
symbol('Device:C_Polarized','C3','100u',116.84,55.88,footprint=EL,label_x=125.73)
symbol('Device:C_Polarized','C4','220u',160.02,88.9,90,EL,label_x=160.02,label_y=77.47)
symbol('Device:R','R1','10',144.78,107.95,footprint='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal')
symbol('Device:C','C5','47n',144.78,121.92,footprint=CAP)
symbol('Connector_Generic:Conn_01x02','J1','AUDIO_IN',60.96,86.36,180,CON,label_x=60.96,label_y=72.39)
symbol('Connector_Generic:Conn_01x02','J2','POWER_6V',60.96,50.8,180,CON,label_x=60.96,label_y=39.37)
symbol('Connector_Generic:Conn_01x02','J3','SPEAKER_8R',193.04,88.9,0,CON,label_x=193.04,label_y=77.47)
symbol('power:PWR_FLAG','#FLG01','PWR_FLAG',81.28,50.8)
symbol('power:PWR_FLAG','#FLG02','PWR_FLAG',81.28,66.04)
# Supply rail and bypass capacitors.
wire((66.04,50.8),(81.28,50.8),(99.06,50.8),(116.84,50.8),(124.46,50.8),(124.46,81.28))
wire((66.04,48.26),(71.12,48.26));label('GND',71.12,48.26)
label('+6V',81.28,50.8)
wire((99.06,50.8),(99.06,52.07));junction(99.06,50.8)
wire((116.84,50.8),(116.84,52.07));junction(116.84,50.8)
wire((99.06,59.69),(99.06,66.04));wire((116.84,59.69),(116.84,66.04),(99.06,66.04),(81.28,66.04))
label('GND',81.28,66.04);junction(99.06,66.04)
# Input path and ground return.
wire((66.04,86.36),(85.09,86.36));label('Audio_In',71.12,86.36)
wire((92.71,86.36),(119.38,86.36));label('Input_Plus',101.6,86.36)
wire((66.04,83.82),(71.12,83.82));label('GND',71.12,83.82)
wire((119.38,91.44),(114.3,91.44),(114.3,104.14));label('GND',114.3,104.14)
wire((124.46,96.52),(124.46,104.14));label('GND',124.46,104.14)
for point in [(127,96.52),(129.54,96.52),(127,81.28)]: nc(*point)
# Output and stabilization network.
wire((134.62,88.9),(144.78,88.9),(156.21,88.9));junction(144.78,88.9);label('IC_Out',139.7,88.9)
wire((163.83,88.9),(187.96,88.9));label('Speaker',170.18,88.9)
wire((187.96,91.44),(187.96,104.14));label('GND',187.96,104.14)
wire((144.78,88.9),(144.78,104.14));wire((144.78,111.76),(144.78,118.11));wire((144.78,125.73),(144.78,132.08));label('GND',144.78,132.08)
text('Single +6 V supply | Gain 20 | External 8-ohm speaker',55.88,25.4,1.8)
text('J2: pin 1 = +6 V; pin 2 = GND. J1/J3: pin 1 = signal; pin 2 = GND.',55.88,142.24)
text('Pins 1 and 8 open: gain 20. Pin 7 open: optional bypass capacitor omitted.',55.88,148.59)
text('C3/C4: electrolytics, at least 10 V. C4 positive lead faces U1 pin 5.',55.88,154.94)
text('Start with a 1 kHz, 20-50 mV peak input. No volume control.',55.88,161.29)
text('Place C2 close to U1 pins 6/4. Verify actual package and component dimensions.',55.88,167.64)
text('Footprints are provisional. PCB is placed but UNROUTED; not fabrication-ready.',55.88,173.99)
schematic=f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_uuid}") (paper "A4")
(title_block (title "LM386N simple audio amplifier") (date "2026-10-26") (rev "A") (comment 1 "Educational project: single +6 V, gain 20"))
(lib_symbols {' '.join(lib.values())})
{' '.join(items)}
(sheet_instances (path "/" (page "1")))
(embedded_fonts no))'''
(OUT/(NAME+'.kicad_sch')).write_text(schematic)
(OUT/(NAME+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':NAME+'.kicad_pro','version':1},'net_settings':{'classes':[{'name':'Default','clearance':0.25,'track_width':0.4,'via_diameter':0.8,'via_drill':0.4}],'meta':{'version':3}}},indent=2)+'\n')
(OUT/'components.json').write_text(json.dumps({'root_uuid':root_uuid,'parts':parts},indent=2)+'\n')
print(OUT/(NAME+'.kicad_sch'))

# Project-local library tables make checks independent of first-run GUI setup.
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7)\n'+''.join(f'(lib (name "{a}") (type "KiCad") (uri "/usr/share/kicad/symbols/{a}.kicad_sym") (options "") (descr ""))\n' for a in dict(libraries))+')\n')
fp_libs=['Package_DIP','Capacitor_THT','Connector_PinHeader_2.54mm','Resistor_THT']
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(f'(lib (name "{a}") (type "KiCad") (uri "/usr/share/kicad/footprints/{a}.pretty") (options "") (descr ""))\n' for a in fp_libs)+')\n')
