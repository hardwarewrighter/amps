"""Generate matching breadboard and PCB previews and the KiCad board."""
from collections import defaultdict, deque
from pathlib import Path
import json
from math import hypot
import random

ROOT = Path(__file__).resolve().parent
# For each terminal: net, breadboard hole, PCB grid x and y (1.27 mm).
PARTS = {
    "J1": ("2.54 mm · 1×8 edge header", "LIN RIN GND +5 L+ R+ L- R-",
           "a2 a4 e1 e3 j1 j3 j5 j7", [(x, 4) for x in range(16, 31, 2)]),
    "RV1": ("20 kΩ audio taper · Bourns PTV09A-1020F-A203", "GND VOL LIN",
            "b1 c8 b2", [(3, 28), (3, 26), (3, 24)]),
    "U1": ("LM358P · DIP-8 and socket", "DRV FB PLUS GND MID BUF BUF +5",
           "e12 e13 e14 e15 f15 f14 f13 f12",
           [(19, 11), (19, 13), (19, 15), (19, 17), (25, 17), (25, 15), (25, 13), (25, 11)]),
    "C1": ("1 µF film · 7.62 mm pitch · ≤5 mm thick", "VOL PLUS", "b8 b6", [(7, 11), (13, 11)]),
    "R1": ("1 kΩ · ¼ W", "FB ACREF", "a13 a9", [(17, 14), (11, 14)]),
    "R2": ("10 kΩ · ¼ W", "FB OUT", "d13 d20", [(18, 8), (24, 8)]),
    "R3": ("47 kΩ · ¼ W", "PLUS BUF", "c14 c19", [(14, 17), (14, 23)]),
    "R4": ("2.2 kΩ · ¼ W", "+5 BN", "h20 h25", [(31, 7), (37, 7)]),
    "R5": ("2.2 kΩ · ¼ W", "BP GND", "h32 h38", [(36, 21), (30, 21)]),
    "R6": ("4.7 Ω · ¼ W", "EN OUT", "c26 c30", [(43, 8), (43, 14)]),
    "R7": ("4.7 Ω · ¼ W", "EP OUT", "b33 b30", [(46, 20), (46, 14)]),
    "R8": ("10 kΩ · ¼ W", "+5 MID", "h10 h15", [(28, 24), (22, 24)]),
    "R9": ("10 kΩ · ¼ W", "MID GND", "i15 i21", [(22, 27), (28, 27)]),
    "R10": ("10 kΩ · ¼ W", "L+ GND", "a39 a44", [(51, 14), (51, 20)]),
    "D1": ("1N4148 · anode, banded cathode", "BN DRV", "f25 f29", [(35, 10), (35, 14)]),
    "D2": ("1N4148 · anode, banded cathode", "DRV BP", "g29 g32", [(37, 14), (37, 18)]),
    "Q1": ("P2N2222A · TO-92 · C, B, E", "+5 BN EN", "e24 e25 e26", [(39, 7), (41, 7), (43, 7)]),
    "Q2": ("P2N2907A · TO-92 · C, B, E", "GND BP EP", "e31 e32 e33", [(40, 23), (42, 23), (44, 23)]),
    "C2": ("100 µF · ≥10 V · Ø ≤6.3 mm · 2.54 mm pitch · +, −", "+5 GND", "j22 j24", [(8, 5), (10, 5)]),
    "C3": ("100 nF ceramic · 2.54 mm pitch", "+5 GND", "i12 i16", [(27, 8), (29, 8)]),
    "C4": ("47 µF · ≥10 V · Ø ≤6.3 mm · 2.54 mm pitch · +, −", "MID GND", "j15 j17", [(23, 20), (25, 20)]),
    "C5": ("47 µF · ≥10 V · Ø ≤6.3 mm · 2.54 mm pitch · +, −", "ACREF GND", "c9 c10", [(10, 19), (8, 19)]),
    "C6": ("470 µF · ≥10 V · Ø ≤10 mm · 5.08 mm pitch · +, −", "OUT L+", "c36 c38", [(52, 8), (48, 8)]),
    "W1": ("Solid wire link · speaker return", "L- GND", "i5 i9", [(28, 2), (30, 2)]),
}

WIDTH, HEIGHT = 57, 32
pitch = 1.27
POT_ORIGIN = PARTS["RV1"][3][0]
POT_MOUNTS = [(7, -6.9), (7, 1.9)]  # mm relative to pin 1
PCB_LINK = ("W2", ["SENSE", "OUT"], [(24, 6), (48, 15)])

def pcb_net(ref, net):
    return "SENSE" if ref == "R2" and net == "OUT" else net


pads = defaultdict(list)
for ref, (_, nets, holes, coordinates) in PARTS.items():
    assert len(nets.split()) == len(holes.split()) == len(coordinates)
    for net, coordinate in zip(nets.split(), coordinates):
        pads[pcb_net(ref, net)].append(tuple(coordinate))
for net, point in zip(PCB_LINK[1], PCB_LINK[2]):
    pads[net].append(point)
all_pads = {point: net for net, points in pads.items() for point in points}
assert len(all_pads) == sum(map(len, pads.values()))


def connect(source, tree, net, occupied, directions):
    pot_clearance = {
        (x, y)
        for i, (px, py) in enumerate(PARTS["RV1"][3])
        if all_pads[px, py] != net
        for x in range(px - 1, px + 2) for y in range(py - 1, py + 2)
        if hypot((x - px) * pitch, (y - py) * pitch - .04 * i) < 1.225
    }
    queue = deque([source])
    previous = {source: None}
    while queue:
        point = queue.popleft()
        if point in tree:
            route = []
            while point is not None:
                route.append(point)
                point = previous[point]
            return route
        x, y = point
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if neighbor in previous or neighbor in pot_clearance or occupied.get(neighbor, net) != net:
                continue
            if 2 <= neighbor[0] <= WIDTH - 2 and 1 <= neighbor[1] <= HEIGHT - 2:
                previous[neighbor] = point
                queue.append(neighbor)
    return []


def route_board():
    rng = random.Random(2222)
    nets = [net for net, points in pads.items() if len(points) > 1]
    best = None
    mount_keepout = {
        (x, y): None for x in range(2, 13) for y in range(20, HEIGHT - 1)
        if any(hypot((x - POT_ORIGIN[0]) * pitch - dx, (y - POT_ORIGIN[1]) * pitch - dy) <= 2.4
               for dx, dy in POT_MOUNTS)
    }
    assert all(point not in all_pads for point in mount_keepout)
    for _ in range(1200):
        rng.shuffle(nets)
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        rng.shuffle(directions)
        occupied = all_pads.copy()
        occupied.update(mount_keepout)
        routes, gaps = [], []
        for net in nets:
            pending = pads[net].copy()
            rng.shuffle(pending)
            tree = {pending.pop()}
            for source in pending:
                route = connect(source, tree, net, occupied, directions)
                if route:
                    if len(route) > 1:
                        routes.append((net, route))
                    tree.update(route)
                    occupied.update(dict.fromkeys(route, net))
                else:
                    gaps.append((net, source, min(tree, key=lambda p: (abs(p[0]-source[0]) + abs(p[1]-source[1]), p))))
                    tree.add(source)
        score = (len(gaps), sum(len(path) for _, path in routes))
        if best is None or score < best[0]:
            best = (score, routes)
    assert best[0][0] == 0, "Unrouted pads"
    return best[1]


routes = route_board()


def strip(hole):
    return (hole[0] >= "f", int(hole[1:]))


def breadboard():
    used, rows, groups = set(), {}, defaultdict(list)
    for _, nets, holes, _ in PARTS.values():
        for net, hole in zip(nets.split(), holes.split()):
            assert hole not in used
            used.add(hole)
            key = strip(hole)
            assert rows.setdefault(key, net) == net, (hole, rows[key], net)
            if key not in groups[net]:
                groups[net].append(key)

    def spare(key):
        for letter in ("jihgf" if key[0] else "abcde"):
            hole = f"{letter}{key[1]}"
            if hole not in used:
                used.add(hole)
                return hole
        raise ValueError(f"No spare holes in strip {key}")

    wires = []
    for net, keys in groups.items():
        if net in ("+5", "GND"):
            wires.extend((net, spare(key), f"{net}:{index * 3 + 2}") for index, key in enumerate(keys))
        else:
            wires.extend((net, spare(first), spare(second)) for first, second in zip(keys, keys[1:]))
    return wires


def segments(path):
    start, previous = path[:2]
    direction = (previous[0] - start[0], previous[1] - start[1])
    for point in path[2:]:
        step = (point[0] - previous[0], point[1] - previous[1])
        if step != direction:
            yield start, previous
            start, direction = previous, step
        previous = point
    yield start, previous


def xy(point):
    return " ".join(f"{v * pitch:.2f}" for v in point)


def route_xy(point):
    pot_points = PARTS["RV1"][3]
    if point in pot_points:
        x, y = POT_ORIGIN
        return f"{x * pitch:.2f} {y * pitch - 2.5 * pot_points.index(point):.2f}"
    return xy(point)


def kicad():
    ids = {net: n for n, net in enumerate(pads, 1)}
    output = ['(kicad_pcb (version 20240108) (generator "pcbnew")',
              '(general (thickness 1.6)) (paper "A4")',
              '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "b.silkscreen")'
              ' (37 "F.SilkS" user "f.silkscreen") (38 "B.Mask" user) (39 "F.Mask" user)'
              ' (44 "Edge.Cuts" user))',
              '(setup (pad_to_mask_clearance 0))']
    output.extend(f'(net {number} "{net}")' for net, number in ids.items())
    output.append(f'(gr_rect (start 0 0) (end {xy((WIDTH, HEIGHT))}) (stroke (width 0.05) (type solid)) (fill none) (layer "Edge.Cuts"))')
    footprints = [(ref, [pcb_net(ref, net) for net in nets.split()], points)
                  for ref, (_, nets, _, points) in PARTS.items()]
    footprints.append(PCB_LINK)
    for ref, nets, points in footprints:
        origin = points[0]
        output.append(f'(footprint "{ref}" (layer "F.Cu") (at {xy(origin)}) (attr through_hole)')
        label_y = 1.7 if ref in ("R3", "W1", "RV1") else -1.7
        label_x = -1.7 if ref == "RV1" else 0
        output.append(f'(fp_text reference "{ref}" (at {label_x} {label_y}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        for n, (net, (x, y)) in enumerate(zip(nets, points), 1):
            shape = 'rect' if n == 1 else 'circle'
            drill = 1.0 if ref in ("J1", "RV1") else 0.8
            offset = f"0 {-2.5 * (n - 1):.2f}" if ref == "RV1" else xy((x-origin[0], y-origin[1]))
            output.append(f'(pad "{n}" thru_hole {shape} (at {offset})'
                          f' (size 1.55 1.55) (drill {drill}) (layers "B.Cu" "B.Mask") (net {ids[net]} "{net}"))')
        if ref == "RV1":
            for x, y in POT_MOUNTS:
                output.append(f'(pad "MP" thru_hole circle (at {x} {y}) (size 3.6 3.6) (drill 2.2) (layers "B.Cu" "B.Mask"))')
            output.append('(fp_rect (start 1 -7.35) (end 13 2.35) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
            output.append('(fp_circle (center 7 -2.5) (end 10 -2.5) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
        output.append(')')
    for net, path in routes:
        for start, end in segments(path):
            output.append(f'(segment (start {route_xy(start)}) (end {route_xy(end)}) (width 0.5) (layer "B.Cu") (net {ids[net]}))')
    output.append(')')
    return "\n".join(output) + "\n"


data = dict(parts=PARTS, wires=breadboard(), width=WIDTH, height=HEIGHT,
            routes=[(net, [list(path[0])] + [list(end) for _, end in segments(path)]) for net, path in routes],
            jumpers=[PCB_LINK], potMounts=POT_MOUNTS)
(ROOT / "layout.js").write_text("const layout = " + json.dumps(data) + ";\n")
(ROOT / "push-pull.kicad_pcb").write_text(kicad())
