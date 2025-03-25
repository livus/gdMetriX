Which symmetry metric to choose?
================================

The proposed symmetry metrics vary fundamentally in their approach.
This page tries to give an overview of all symmetry metrics for graph drawings previously published in order to ease the decision on what metric might be most suitable for your specific use case.

In general we distinguish for different types of symmetry - reflective, rotational, translative and dihedral.

An overview of all identified symmetry metrics can be seen in the table below, most of which are implemented in gdMetriX.

+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
|             Metric             |                                                                                                         Description                                                                                                         |                Source                | Implementation                                  |
+================================+=============================================================================================================================================================================================================================+======================================+=================================================+
| Node-based symmetry            | Tries to identify all potential axes over all vertex pairs and build the sum over all axes over a certain quality threshold.                                                                                                | :cite:t:`purchase_metrics_2002`      | :func:`symmetry.reflective_symmetry`            |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
| Edge-based symmetry            | This metric tries to improve upon the node-based symmetry by also considering edges.                                                                                                                                        | :cite:t:`chapman_symmetry_2018`      | :func:`symmetry.edge_based_symmetry`            |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
| Stress                         | Based on the classic term of *stress*, i.e. the ratio of the edge lengths, this measure tries to define a measure of energy in a drawing, with lower energy levels claimed to correspond to more symmetric drawings.        | :cite:t:`welch_measuring_2017`       | :func:`symmetry.stress`                         |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
| Even neighborhood distribution | Determines how evenly the neighbors of each vertex are distributed among each vertex.                                                                                                                                       | :cite:t:`xu_force-directed_2018`     | :func:`symmetry.even_neighborhood_distribution` |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
| Automorphism detection         | Tries to determine the extent to which a drawing displays an automorphism or a group of automorphisms, meaning that this metric takes the structural symmetry of the graph into account.                                    | :cite:t:`meidiana_automorphism_2022` |                                                 |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+
| Pixel-based symmetry           | A novel approach using the pixel drawing of the graph to estimate symmetry.                                                                                                                                                 |                                      | :func:`symmetry.visual_symmetry`                |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+-------------------------------------------------+

Comparison
----------

.. note::
    For a more in-depth theoretical comparison of different symmetry metrics refer to :download:`this guide<_static/symmetry_guide.pdf>`.


A more in-depth comparison between the node-, edge-, and stress-based approaches can be seen in the corresponding study by :cite:t:`welch_measuring_2017`.
They concluded, that the node-based metric agreed with human perception
of symmetry slightly more often compared to the edge-based metric. The stress-based metric
did not outperform either of the other metrics.

A more basic overview of the properties of all metrics is given in the following table.

+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
|             Metric             | Type of symmetry                    | Runtime             | Scope  | Robust    | Faithful |
+================================+=====================================+=====================+========+===========+==========+
| Node-based symmetry            | Reflective                          | :math:`O(n^7)`      | Both   | Partially | No       |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
| Edge-based symmetry            | Reflective, translative, rotational | :math:`O(m^2)`      | Both   | No        | No       |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
| Stress                         | n.a.                                | :math:`O(n^2)`      | Local  | Yes       | Yes      |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
| Even neighborhood distribution | n.a.                                | :math:`O(n^2)`      | Local  | Yes       | Yes      |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
| Automorphism detection         | Reflective, translational           | :math:`O(n \log n)` | Local  | Yes       | Yes      |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+
| Pixel-based symmetry           | Reflective, rotational, dihedral    | :math:`O(n + m)`    | Global | No        | No       |
+--------------------------------+-------------------------------------+---------------------+--------+-----------+----------+


**Types of symmetry.** Three main types of symmetry are distinguished in literature :cite:`biedl_perception_2018`.
If a pattern exhibits *reflective* symmetry, it is mirrored along
an axis. If a pattern exhibits *rotational* symmetry, if it remains
unchanged after rotating it around a central point for a given
angle :math:`α < 360^\circ`. A pattern exhibits *translational* symmetry if
it remains unchanged after applying a shift transformation.

**Scope.** The neural symmetry only considers global symmetry axes. As
the node- and edge-based approaches integrate a multitude of axes into the final value, some axes might
represent more local substructures while others reflect global structures. The edge-based symmetry
has the advantages that the number of considered axes can be customised. With a lower number
of axes, it is expected that only the strongest, i.e. global, symmetries are considered. More subtle,
local symmetries might be considered as well. The node-based symmetry metric does not offer such
trade-offs. All other metrics are based on local substructures. It is, however, unclear to what extend
global symmetry emerges from a sum of local symmetries.

**Robustness.** A metric is *robust* if it is not influenced by the scale, rotation or translation of the
drawing :cite:p:`welch_measuring_2017`. A metric should aim to be robust, as the perceived symmetry does not change with such
modifications. Unfortunately, the edge-based symmetry and the neural symmetry are not inherently
robust to rescaling, the node-based metric can be made robust by wisely choosing appropriate
parameters. All other metrics are inherently robust to rescaling, rotation and translation.

**Faithfulness.** A metric is *faithful*, if it is able to detect whether the depicted symmetries match the
inherit symmetries of the graph itself :cite:p:`meidiana_automorphism_2022`. The automorphism metric was designed with that exact
goal in mind. The stress- and force-based approaches consider the structure of the graph as well, the
extend to which it influences the final metric, however, has to be evaluated separately.

Runtime
-------

Especially when used iteratively in an automatic embedder, a symmetry metric has to be quick to obtain.
However, especially the node- and edge-based metrics - with a runtime of :math:`O(n^7)` and :math:`O(m^2)` respectively are infeasible to obtain for bigger instances.

To compare the runtime, we generated random graphs with edge densities from 10% up to 90% (see the figure below).

.. figure:: images/sym_runtime_all.svg
  :width: 90%
  :align: center
  :alt: Runtime comparison of all metrics

  Runtime comparison of all metrics


When focusing only on the faster metrics, we can see that the stress-based approach takes a bit longer compared to the rest. This is due to the additional binary search that is done to minimize the final metric as discussed above.

.. figure:: images/sym_runtime.svg
  :width: 90%
  :align: center
  :alt: Runtime comparison of the faster metrics

  Runtime comparison of the faster metrics


Correlation
-----------

In case all metrics are capable of measuring some sense of symmetry, we expect that they exhibit some extend of correlation.

The correlation between all symmetry metrics are depicted below.
The data consists of random graphs embedded using the force-based embedder from networkX.

.. figure:: images/sym_scatter.svg
  :width: 90%
  :align: center
  :alt: Scatter plot

  Scatter plot between all implemented symmetry metrics

.. figure:: images/sym_corr.svg
  :width: 90%
  :align: center
  :alt: Correlation matrix

  Correlation matrix between all implemented symmetry metrics


Correlation to other metrics
----------------------------

Some symmetry metrics might highly depend on, i.e., the density or size of a graph.

See the scatter plot below to evaluate of a specific metric is right for you.

.. figure:: images/sym_scatter_2.svg
  :width: 90%
  :align: center
  :alt: Scatter plot

.. figure:: images/sym_corr_2.svg
  :width: 90%
  :align: center
  :alt: Correlation matrix

  Scatter plot between all implemented symmetry metrics



Bibliography
---------------------
.. bibliography::