"""
nodes2geojson.py - convert FCVOM .dat grid to geojson

Usage:

python nodes2geojson.py 26916 somegrid.dat somegrid.geojson

Replace 26916 with the EPSG code for your projection.

File format is a line specifying number of nodes, then a line specifying
number of cells, then a listing of cells, then a listing of nodes.

Cells are

  i n0 n1 n2 1

where i is the cell number, n0 - n2 are the numbers of the nodes, and 1
is a 1, don't know what it means.

Nodes (vertices) are

  i x y depth

where is is the node number, and x, y, and depth are x, y, and depth.

The assert statements verify / enforce that the cell and node numbers start at
one and go up without gaps, if the asserts fail, will need to change code to
use a dict instead of a list.

Terry N. Brown terrynbrown@gmail.com Tue Nov 19 03:09:33 UTC 2019
"""

import json
import sys
from collections import namedtuple
from pyproj import Transformer

Node = namedtuple("Node", "num x y depth")
Cell = namedtuple("Cell", "num n0 n1 n2 one")


def main():
    pEPSG, pIN, pOUT = sys.argv[1:]  # read 3 command line parameters
    # a Transformer object that transforms pEPSG coords to 4326 (WGS84)
    trans = Transformer.from_crs(int(pEPSG), 4326, always_xy=True)
    nodes = []  # vertices
    cells = []
    with open(pIN) as in_:
        nodes_n = int(next(in_).split()[-1])  # read "Node Number = 5795" line
        cells_n = int(next(in_).split()[-1])  # read "Cell Number = 10678" line
        for cell_i in range(1, cells_n + 1):  # read cells
            cells.append(Cell._make(map(int, next(in_).split())))  # 5 ints
            assert cells[-1].num == cell_i, (cells[-1].num, cell_i)
        for node_i in range(1, nodes_n + 1):  # read nodes
            node = Node._make(map(float, next(in_).split()))  # read 4 floats
            assert node.num == node_i, (node.num, node_i)
            # transform the x,y and store num,x',y',depth
            nodes.append(
                Node._make(
                    [node.num]
                    + list(trans.transform(node.x, node.y))
                    + [node.depth]
                )
            )

    # top level of GeoJSON structure
    geojson = {"type": "FeatureCollection", "features": []}
    for cell_i, cell in enumerate(cells):
        # .dat file numbers things from 1, Python numbers things from 0
        # so cell_i is 1 less than .dat file cell number, and node numbers
        # are 1 more than Python list indices in node list.
        coords = []
        props = {}
        # make new feature structure and append to features list
        feature = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": props,
        }
        geojson['features'].append(feature)
        depths = []
        # repeat first as last to close poly
        for corner in cell.n0, cell.n1, cell.n2, cell.n0:
            coords.append([nodes[corner - 1].x, nodes[corner - 1].y])
            depths.append(nodes[corner - 1].depth)
        # first depth got repeated, so
        del depths[-1]
        props['mindpth'] = min(depths)
        props['maxdpth'] = max(depths)
        props['meandpth'] = sum(depths) / len(depths)
        props['cell_i'] = cell_i + 1

    # write the result
    with open(pOUT, 'w') as out:
        json.dump(geojson, out)


if __name__ == "__main__":
    main()
