<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://livus.github.io/gdMetriX/_static/logo_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://livus.github.io/gdMetriX/_static/logo.svg">
  <img src="https://livus.github.io/gdMetriX/_static/logo.svg" alt="gdMetriX logo">
</picture>

# gdMetriX: Graph Drawing Quality Metrics for Python & NetworkX

**gdMetriX** is a Python library and [NetworkX](https://github.com/networkx/networkx) extension for computing
**graph drawing quality metrics** — also known as graph layout aesthetics, readability metrics, or graph
embedding quality measures. It implements peer-reviewed metrics from the graph drawing and information
visualization literature (crossing number, crossing density, symmetry, node distribution, edge orthogonality,
angular resolution, and more) so you can quantitatively evaluate, compare, and benchmark graph layouts and
graph drawing algorithms.

[![PyPI](https://img.shields.io/pypi/v/gdMetriX.svg)](https://pypi.org/project/gdMetriX/)
[![Tests](https://github.com/livus/gdMetriX/actions/workflows/tests.yml/badge.svg)](https://github.com/livus/gdMetriX/actions/workflows/tests.yml)
[![Python](https://img.shields.io/pypi/pyversions/gdMetriX.svg)](https://pypi.org/project/gdMetriX/)
[![NumPy](https://img.shields.io/badge/works%20with-networkX-013243?logo=python)](https://github.com/networkx/networkx)
[![Downloads](https://img.shields.io/pypi/dm/gdMetriX)](https://pypistats.org/packages/gdmetrix)
[![Coverage](https://codecov.io/gh/livus/gdMetriX/branch/main/graph/badge.svg)](https://app.codecov.io/gh/livus/gdMetriX)
[![License](https://img.shields.io/github/license/livus/gdMetriX.svg)](https://github.com/livus/gdMetriX?tab=GPL-3.0-1-ov-file)
[![GitHub Pages](https://img.shields.io/badge/docs-github.io-blue.svg)](https://livus.github.io/gdMetriX/)
[![Paper](https://img.shields.io/badge/DOI-10.4230%2FLIPIcs.GD.2024.45-blue)](https://doi.org/10.4230/LIPIcs.GD.2024.45)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/index.html)
[![PRs Welcome](https://img.shields.io/badge/contribute-good%20first%20issues-brightgreen.svg)](https://github.com/livus/gdMetriX/issues?q=is%3Apr+is%3Aopen+label%3A%22good+first+issue%22)

📖 **[Full documentation](https://livus.github.io/gdMetriX/)** · 📦 **[PyPI package](https://pypi.org/project/gdMetriX/)** · 📄 **[Cite the paper](#citing)** · 🕹️ **[Try the live graph editor](http://livus.sytes.net/apps/graph)**

## Why gdMetriX?

If you draw, lay out, embed, or visualize graphs and networks — and need to answer "how good is this layout?" —
gdMetriX gives you a ready-made, tested toolkit instead of re-implementing graph drawing metrics from papers
yourself:

- **Drop-in NetworkX integration** — works directly with `networkx.Graph` / `DiGraph` objects and node `pos`
  attributes, no custom graph format required.
- **Broad metric coverage** — crossings, area & boundary, node distribution, edge directions, and symmetry
  metrics, each backed by a citation to the original publication.
- **Benchmark datasets included** — one-line access to the
  [Graph Layout Benchmark Datasets](https://visdunneright.github.io/gd_benchmark_sets/), so you can evaluate
  algorithms on real-world graphs (subway maps, code dependency graphs, Rome graphs, chess openings, SteinLib, and
  more) without manually downloading and parsing data.
- **Built for research** — used to support reproducible evaluation of graph layout / graph embedding algorithms;
  citable via a [Dagstuhl / LIPIcs publication](https://doi.org/10.4230/LIPIcs.GD.2024.45).

Typical use cases: evaluating graph layout/graph drawing algorithms, comparing force-directed vs. orthogonal vs.
hierarchical layouts, scoring auto-generated diagrams, building graph visualization quality dashboards, and
academic research in graph drawing and network visualization.

## Table of contents

- [Installation](#installation)
- [Examples](#examples)
- [Implemented metrics](#implemented-metrics)
- [Loading benchmark datasets](#loading-datasets)
- [Interactive graph editor](#interactive-graph-editor)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Citing](#citing)
- [License](#license)

## Installation

gdMetriX requires Python 3.9 or higher.

Before installing, make sure you have the latest version of `pip` installed:

```shell
python -m pip install --upgrade pip
```

To install the package using `pip` use the following command:

```shell
pip install gdMetriX
```

## Examples

### Working with networkX

gdMetriX works with the graph classes of networkX. For more details on how to work with networkX, please refer to their
[documentation](https://networkx.org/documentation/stable/).

For all graph drawing metrics, gdMetriX needs node positions, which is expected as a tuple with the attribute name '
pos'.
You can set the attributes using networkX:

```python
import networkx as nx
import gdMetriX

g = nx.Graph()
g.add_node('nodeA')
g.add_node('nodeB')
pos = {'nodeA': (0, 3.5), 'nodeB': (-3, 3)}
nx.set_node_attributes(g, pos)
```

Alternatively you can also set the position for a individual vertex:

```python
g.add_node('nodeC', pos=(0, 0))
```

### Calculating quality metrics

For a complete list of implemented metrics, please refer to the [documentation](https://livus.github.io/gdMetriX/metrics.html).

For an example, in order to calculate the number of crossings, use:

```python
crossings = gdMetriX.get_crossings(g)
print(len(crossings))
```

The node positions are automatically read from the graph. You can also supply them directly:

```python
pos = {'nodeA': (0, 3.5), 'nodeB': (-3, 3), 'nodeC': (0, 0)}
crossings = gdMetriX.get_crossings(g, pos=pos)
print(len(crossings))
```

Other graph drawing metrics follow the same pattern — for example, crossing density, edge orthogonality and
reflective symmetry:

```python
crossing_quality = gdMetriX.crossing_density(g)
orthogonality = gdMetriX.edge_orthogonality(g)
symmetry_score = gdMetriX.reflective_symmetry(g)
```

## Implemented metrics

gdMetriX implements graph drawing quality metrics across five categories. Each metric links to its
implementation and the publication it is based on in the [full metrics reference](https://livus.github.io/gdMetriX/metrics.html).

| Category | Example metrics |
|---|---|
| **Crossings** | crossing number, crossing list, crossing density, crossing angles, crossing angular resolution |
| **Area & boundary** | bounding box area, tight (convex hull) area, width, height, aspect ratio |
| **Node distribution** | center of mass, closest pair of points/elements, concentration, homogeneity, horizontal/vertical balance, node orthogonality, Gabriel ratio |
| **Edge directions** | angular resolution, average flow, upwards flow, coherence to average flow, edge orthogonality |
| **Symmetry** | reflective (node-based) symmetry, edge-based symmetry, stress-based symmetry, even neighborhood distribution, visual symmetry |

gdMetriX also includes supporting utilities for graph drawing research: planarization, position normalization,
combinatorial embeddings, ordered neighborhoods, and heatmap generation for local metrics. See the
[additional features reference](https://livus.github.io/gdMetriX/additional_features.html) for details.

## Loading datasets

gdMetriX supports the automatic import of graph drawing datasets. The datasets are collected from the
[Graph Layout Benchmark Datasets](https://visdunneright.github.io/gd_benchmark_sets/) project from the Northeastern
University Visualization Lab easily accessible for networkX.

The project aims to collect datasets used for graph layout algorithms and make them available for long-term access.
The graphs are stored on the [Open Science Foundation platform](https://osf.io/j7ucv/).

Information about the individual datasets can be found at the
[project homepage](https://visdunneright.github.io/gd_benchmark_sets/).

To get a list of all available datasets:

```python
available_datasets = gdMetriX.get_available_datasets()
print(available_datasets)
# ['subways', 'code', 'rome', 'chess', 'steinlib', ...]
```

To iterate over all graphs of a given dataset, simply call `gdMetriX.iterate_dataset()`:

```python
for graph in gdMetriX.iterate_dataset('subways'):
    print(graph.nodes())
```

## Interactive graph editor

Want to try gdMetriX without writing any code? The
**[live interactive graph editor](http://livus.sytes.net/apps/graph)** lets you draw or import a graph in your
browser and see gdMetriX's quality metrics (crossings, symmetry, node distribution, edge orthogonality, and more)
calculated and updated live as you edit the layout.

## Documentation

The full API reference, tutorial notebooks, and the complete list of implemented graph drawing metrics are
available at **[livus.github.io/gdMetriX](https://livus.github.io/gdMetriX/)**.

## Contributing

Contributions are welcome! Whether it's a new metric, a bug fix, a documentation improvement, or a new dataset
integration, feel free to open an issue or pull request. New to the project? Start with an
[issue labeled "good first issue"](https://github.com/livus/gdMetriX/issues?q=is%3Apr+is%3Aopen+label%3A%22good+first+issue%22).

## Citing

If you find this project useful for your work, consider citing the corresponding
[Dagstuhl publication](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.GD.2024.45).

```bibtex
@InProceedings{nollenburg_et_al:LIPIcs.GD.2024.45,
  author    = {N\"ollenburg, Martin and R\"oder, Sebastian and Wallinger, Markus},
  title     = {{GdMetriX - A NetworkX Extension For Graph Drawing Metrics}},
  booktitle = {32nd International Symposium on Graph Drawing and Network Visualization (GD 2024)},
  pages     = {45:1--45:3},
  series    = {Leibniz International Proceedings in Informatics (LIPIcs)},
  ISBN      = {978-3-95977-343-0},
  ISSN      = {1868-8969},
  year      = {2024},
  volume    = {320},
  editor    = {Felsner, Stefan and Klein, Karsten},
  publisher = {Schloss Dagstuhl -- Leibniz-Zentrum f\"ur Informatik},
  address   = {Dagstuhl, Germany},
  doi       = {10.4230/LIPIcs.GD.2024.45}
}
```

## License

The project is distributed under the GNU General Public License Version 3.
