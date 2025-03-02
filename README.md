<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://livus.github.io/gdMetriX/_static/logo_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://livus.github.io/gdMetriX/_static/logo.svg">
  <img src="https://livus.github.io/gdMetriX/_static/logo.svg" alt="gdMetriX">
</picture>


[![PyPI](https://img.shields.io/pypi/v/gdMetriX.svg)](https://pypi.org/project/gdMetriX/)
![Python](https://img.shields.io/pypi/pyversions/gdMetriX.svg)
[![NumPy](https://img.shields.io/badge/works%20with-networkX-013243?logo=python)](https://github.com/networkx/networkx)
![Downloads](https://img.shields.io/pypi/dm/gdMetriX)
![Coverage](https://codecov.io/gh/livus/gdMetriX/branch/main/graph/badge.svg)
![License](https://img.shields.io/github/license/livus/gdMetriX.svg)
[![GitHub Pages](https://img.shields.io/badge/docs-github.io-blue.svg)](https://livus.github.io/gdMetriX/)
[![Paper](https://img.shields.io/badge/DOI-10.4230%2FLIPIcs.GD.2024.45-blue)](https://doi.org/10.4230/LIPIcs.GD.2024.45)
![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)


gdMetriX is an extension to [networkX](https://github.com/networkx/networkx) providing commonly used quality measures in
graph drawing as well as access to some datasets used previously for evaluating graph embedding algorithms.

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

For a complete list of implemented metrics, please refer to the documentation.

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

### Loading datasets

gdMetriX supports the automatic import of graph drawing datasets. The datasets are collected from the
[Graph Layout Benchmark Datasets](https://visdunneright.github.io/gd_benchmark_sets/) project from the Northeastern
University Visualization Lab easily accessible for networkX.

The project aims to collect datasets used for graph layout algorithms and make them available for long-term access.
The graphs are stored on the [Open Science Foundation platform](https://osf.io/j7ucv/).

Information about the individual datasets can be found at the
[project homepage](https://visdunneright.github.io/gd_benchmark_sets/>).

To get a list of all available datasets:

```python
>> > available_datasets = get_available_datasets()
>> > print(available_datasets)
['subways', 'code', 'rome', 'chess', 'steinlib', ...
```

To iterate over all graphs of a given dataset, simply call :func:`get_list_of_graphs()`:

```python
>> > for graph in get_list_of_graphs('subways'):
    >> > print(graph.nodes())
```        

## License

The project is distributed under the GNU General Public License Version 3.


## Citing

If you find this project useful for your work, consider citing the corresponding
[Dagstuhl publication](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.GD.2024.45>).