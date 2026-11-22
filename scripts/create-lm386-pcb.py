#!/usr/bin/env python3
"""Create a placed, unrouted learning board from the validated schematic export.
Run create-lm386-kicad.py and export its netlist to /tmp/lm386-simple.xml first.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pcbnew

root=Path(__file__).resolve().parent.parent
out=root/'circuits/lm386-simple'
meta=json.loads((out/'components.json').read_text())
board=pcbnew.BOARD()
netmap={}
padnets={}
for item in ET.parse('/tmp/lm386-simple.xml').findall('./nets/net'):
    name=item.attrib['name']
    if name.startswith('unconnected-'):continue
    net=pcbnew.NETINFO_ITEM(board,name)
    board.Add(net)
    netmap[name]=net
    for node in item.findall('node'):
        padnets[node.attrib['ref'],node.attrib['pin']]=net
places={'U1':(120,100),'J1':(104,103),'J2':(104,88),'J3':(140,100),
        'C1':(110,104),'C2':(114,97),'C3':(112,89),'C4':(135,96),
        'R1':(128,112),'C5':(136,112)}
for component in meta['parts']:
    if not component['footprint']:continue
    library,name=component['footprint'].split(':')
    fp=pcbnew.FootprintLoad(f'/usr/share/kicad/footprints/{library}.pretty',name)
    if fp is None:raise RuntimeError(component['footprint'])
    fp.SetFPID(pcbnew.LIB_ID(library,name))
    fp.SetReference(component['ref']);fp.SetValue(component['value'])
    fp.SetPath(pcbnew.KIID_PATH('/'+meta['root_uuid']+'/'+component['uuid']))
    fp.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(x) for x in places[component['ref']]]))
    board.Add(fp)
    for pad in fp.Pads():
        key=component['ref'],pad.GetNumber()
        if key in padnets:pad.SetNet(padnets[key])
for a,b in [((98,82),(148,82)),((148,82),(148,122)),((148,122),(98,122)),((98,122),(98,82))]:
    edge=pcbnew.PCB_SHAPE();edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
    edge.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(x) for x in a]))
    edge.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(x) for x in b]))
    edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.05));board.Add(edge)
board.BuildConnectivity()
pcbnew.SaveBoard(str(out/'lm386-simple.kicad_pcb'),board)
print('Created placed UNROUTED board. Footprint dimensions require verification.')
