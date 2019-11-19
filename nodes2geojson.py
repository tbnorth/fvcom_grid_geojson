"""
nodes2geojson.py - convert FCVOM .dat grid to geojson

Usage:

python nodes2geojson.py 26916 somegrid.dat somegrid.geojson

Replace 26916 with the EPSG code for your projection.

File format is a line specifying number of nodes, then a line specifying
number of cells, then a listing of cells, then a listing of nodes.

Cells are

  i n0 n1 n2 1

where i is the cell number, n0 - n2 are the numbers of the vertices, and 1
is a 1, don't know what it means.

Nodes (vertices) are

  i x y d

where is is the node number, and x, y, and d are x, y, and depth.

The assert statements verify / enforce that the cell and node numbers start at
one and go up without gaps, if the asserts fail, will need to change code to
use a dict instead of a list.

Terry N. Brown terrynbrown@gmail.com Tue Nov 19 03:09:33 UTC 2019
"""

import json
import sys
from pyproj import Transformer


def main():
    pEPSG, pIN, pOUT = sys.argv[1:]
    trans = Transformer.from_crs(int(pEPSG), 4326, always_xy=True)
    vertice = []  # nodes
    cell = []
    geojson = {"type": "FeatureCollection", "features": []}
    in_file = pIN
    out_file = pOUT
    with open(in_file) as in_:
        nodes_n = next(in_)  # read "Node Number = 5795" line
        nodes_n = int(nodes_n.split()[-1])
        cells_n = next(in_)  # read "Cell Number = 10678" line
        cells_n = int(cells_n.split()[-1])
        for cell_i in range(1, cells_n + 1):  # read cells
            vals = list(map(float, next(in_).split()))
            assert vals[0] == cell_i, (vals[0], cell_i)
            cell.append(list(map(int, vals[1:4])))
        for node_i in range(1, nodes_n + 1):  # read nodes
            vals = list(map(float, next(in_).split()))
            assert vals[0] == node_i, (vals[0], node_i)
            vertice.append(list(trans.transform(*vals[1:3])) + vals[-1:])
    with open(out_file, 'w') as out:
        for cell_i, cell in enumerate(cell):
            coords = []
            props = {}
            feature = {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": props,
            }
            geojson['features'].append(feature)
            # first two elements of each vertice
            coords.extend(vertice[i - 1][:2] for i in cell[:3])
            # repeat first as last to close poly
            coords.append(vertice[cell[0] - 1][:2])
            # last element of each vertice
            depths = [vertice[i - 1][-1] for i in cell[:3]]
            props['mindpth'] = min(depths)
            props['maxdpth'] = max(depths)
            props['meandpth'] = sum(depths) / len(depths)
            props['cell_i'] = cell_i + 1
        json.dump(geojson, out)


if __name__ == "__main__":
    main()
