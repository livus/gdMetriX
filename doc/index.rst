Welcome to gdMetriX's documentation!
=====================================


gdMetriX is an extension to
`networkX <https://github.com/networkx/networkx>`__ providing commonly
used quality measures in graph drawing as well as access to
datasets used previously for evaluating graph embedding algorithms.

For a complete list of implemented metrics and features, refer to the :ref:`metrics-label` page.

Installation
------------

gdMetriX requires Python 3.9 or higher.

To install the package using ``pip`` use the following command:

.. code:: shell

   pip install gdMetriX

Examples
--------

For more examples refer to the Tutorial.

Working with networkX
~~~~~~~~~~~~~~~~~~~~~

gdMetriX works with all graph classes of networkX. For more details on
how to work with networkX, please refer to the
`documentation <https://networkx.org/documentation/stable/>`__ of networkX.

gdMetriX works on embeddings of graphs, for which node positions are
required, which are expected as a tuple with the attribute name ‘pos’.
You can set the attributes using networkX:

.. code:: python

   import networkx as nx
   import gdMetriX

   g = nx.Graph()
   g.add_node('nodeA')
   g.add_node('nodeB')
   pos = {'nodeA': (0, 3.5), 'nodeB': (-3, 3)}
   nx.set_node_attributes(g, pos)

Alternatively you can also set the position for each vertex individually:

.. code:: python

   g.add_node('nodeC', pos=(0, 0))

Calculating quality metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a complete list of implemented metrics, please refer to the
:ref:`metrics-label` page.

In order to calculate for example the quality of a drawing in
regards to crossing, use:

.. code:: python

   crossing_quality = gdMetriX.crossing_density(g)
   print(crossing_quality)

The node positions are automatically read from the graph. You can also
supply them directly:

.. code:: python

   pos = {'nodeA': (0, 3.5), 'nodeB': (-3, 3), 'nodeC': (0, 0)}
   crossing_quality = gdMetriX.crossing_density(g, pos)
   print(crossing_quality)

Loading datasets
~~~~~~~~~~~~~~~~

gdMetriX supports the automatic import of graph drawing datasets. The
datasets are collected from the `Graph Layout Benchmark
Datasets <https://visdunneright.github.io/gd_benchmark_sets/>`__ project
from the Northeastern University Visualization Lab easily accessible for
networkX.

The project aims to collect datasets used for graph layout algorithms
and make them available for long-term access. The graphs are stored on
the `Open Science Foundation platform <https://osf.io/j7ucv/>`__.

Information about the individual datasets can be found at the `project
homepage <https://visdunneright.github.io/gd_benchmark_sets/%3E>`__.

To get a list of all available datasets:

.. code:: python

   >>> available_datasets = get_available_datasets()
   >>> print(available_datasets)
   ['subways', 'code', 'rome', 'chess', 'steinlib', ...

To iterate over all graphs of a given dataset, simply call
:func:`gdMetriX.get_list_of_graphs()`:

.. code:: python

   >>> for graph in gdMetriX.get_list_of_graphs('subways'):
   >>>    print(graph.nodes())

License
-------

The project is distributed under the GNU General Public License version 3.

..
    Citing
    ------

    If you find this project useful for your work, consider citing it::

        @Misc{Noellenburg2024gdMetriX,
            author       = {Martin Nöllenburg, Markus Wallinger, Sebastian Röder},
            howpublished = {Under submission to Graph Drawing Posters},
            title        = {gdMetriX},
            year         = {2024},
            url          = {https://livus.github.io/gdMetriX/},
        }





.. toctree::
   :maxdepth: 1
   :caption: Contents:

   tutorial_overview
   features
   modules

.. Indices and tables
.. ==================
..
.. * :ref:`genindex`
.. * :ref:`modindex`
