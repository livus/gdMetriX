# gdMetriX
#
# Copyright (C) 2025  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module makes graphs collected by the
'`Graph Layout Benchmark Datasets <https://visdunneright.github.io/gd_benchmark_sets/>`_'
project from the Northeastern University Visualization Lab easily accessible for networkX.

The project aims to collect datasets used for graph layout algorithms and make them available for
long-term access.
The graphs are stored on the `Open Science Foundation platform <https://osf.io/j7ucv/>`_

Information about the individual datasets can be found at the
`project homepage <https://visdunneright.github.io/gd_benchmark_sets/>`_.
For more information refer to the
corresponding `short paper <https://osf.io/preprints/osf/yftju>`_
:footcite:p:`DiBartolomeo2023CollectionBenchmarkDatasets`.

Usage
--------

To get a list of all available datasets, call :func:`get_available_datasets()`:

.. code-block:: python

    >>> available_datasets = get_available_datasets()
    >>> print(available_datasets)
    ['subways', 'code', 'rome', 'chess', 'steinlib', ...

To iterate over all graphs of a given dataset, simply call :func:`iterate_dataset()`:

.. code-block:: python

    >>> for name, g in iterate_dataset('subways'):
    >>>     print("'{name}' has {n} vertices and {m} edges".format(name=name, n=g.order(), m=len(g.edges()))

The module takes care of downloading, caching, maintaining and updating the graphs automatically.
In case there are any problems or you want to free up disc space, you can clean all saved data
with the following command:

.. code-block:: python

    >>> clear_cache()

Methods
-------
"""
import json
import os
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import gettempdir
from typing import List, Iterator, Tuple, Any

import networkx as nx
import osfclient
from osfclient import cli


def _get_data_dir():
    temp_dir = Path(gettempdir()) / "gdMetriX_d207f7c5-18c9-4840-8945-2e81eb582ce5/"
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


@dataclass
class _OsfClientArgs:
    def __init__(
        self,
        project,
        username=None,
        update=True,
        force=False,
        destination=None,
        source=None,
        recursive=False,
        target=None,
        output=None,
        remote=None,
        local=None,
    ):
        self.project = project
        self.username = username
        self.update = update  # applies to upload, clone, and fetch
        self.force = force  # applies to fetch and upload
        # upload arguments:
        self.destination = destination
        self.source = source
        self.recursive = recursive
        # remove arguments:
        self.target = target
        # clone arguments:
        self.output = output
        # fetch arguments:
        self.remote = remote
        self.local = local

    @classmethod
    def default(cls):
        return _OsfClientArgs(
            # username='g.alejo@alumni.ubc.ca',
            project="j7ucv",
            # upload arguments:
            destination="",
            source="",
            # remove argument:
            target="",
            # clone argument:
            output="",
            # fetch arguments:
            remote="",
            local="",
        )


def _get_project():
    osf = osfclient.OSF()
    return osf.project("j7ucv")


def _get_available_files_from_server(proj):
    available_files = []

    for x in proj.storage().folders:
        if x.name == "nx_json":
            for y in x.files:
                available_files.append(y)
            break

    return available_files


class _AvailableFiles:
    _path = _get_data_dir() / "available_datasets.json"

    def __init__(self, created: datetime, checked: datetime, available_files: Any):
        self.created = created
        self.checked = checked
        self.available_files = available_files

    @classmethod
    def load(cls):
        if not _AvailableFiles._path.exists():
            available_files = _AvailableFiles(datetime.min, datetime.min, [])
            available_files.save()
            return available_files

        with open(_AvailableFiles._path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data.get("created"), str):
            data["created"] = datetime.fromisoformat(data["created"])
        if isinstance(data.get("checked"), str):
            data["checked"] = datetime.fromisoformat(data["checked"])

        return cls(**data)

    def save(self):
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # Convert datetime to string
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(
            _get_data_dir() / "available_datasets.json", "w", encoding="utf-8"
        ) as f:
            json.dump(self.__dict__, f, indent=4, default=custom_serializer)


def clear_cache() -> None:
    """
    In case that there any issues with corrupted data, call this method
    to clear all graphs saved to the disk.
    """
    shutil.rmtree(_get_data_dir())


def _get_available_datasets():
    def _newer_version_exists(available_files: _AvailableFiles) -> bool:
        # If the dataset was last checked within the last 30 minutes we assume nothing
        # has changes to avoid spamming OSF and risking a 429 HTTP status code
        if datetime.now() - available_files.checked < timedelta(minutes=30):
            return False

        # Perform check

        # Update last checked
        available_files.checked = datetime.now()
        available_files.save()

        try:
            project = _get_project()
            last_modified = datetime.strptime(
                project.date_modified.split(".")[0], "%Y-%m-%dT%H:%M:%S"
            )
        except:
            # If we cannot even obtain the project info we are unlikely to re-download it
            # -> return False to be save
            return False

        return last_modified > available_files.created

    available_files = _AvailableFiles.load()

    # Try to get the list of available files from the .json
    if _newer_version_exists(available_files):
        # Delete everything to trigger a re-download
        clear_cache()

        # Try to download them from OSF
        proj = _get_project()
        available_files.available_files = [
            filedata.path for filedata in _get_available_files_from_server(proj)
        ]
        available_files.created = datetime.now()
        available_files.save()

    dic = {}
    for file in available_files.available_files:
        dic[os.path.basename(file).split(".")[0]] = file
    return dic


def _ensure_dataset_downloaded(name: str) -> None:
    all_files = _get_available_datasets()
    remote_path = all_files[name]
    sub_folder = _get_data_dir() / name
    local_path = _get_data_dir() / (name + ".tar.gz")

    # If the sub_folder already exists, we assume that everything is already downloaded
    if sub_folder.exists() and len(os.listdir(sub_folder)) > 0:
        return

    # Download the zipped directory
    arguments = _OsfClientArgs.default()
    arguments.remote = remote_path
    arguments.local = local_path
    arguments.force = True
    cli.fetch(arguments)

    # Unzip
    with tarfile.open(str(local_path), "r:gz") as tar:
        tar.extractall(path=str(sub_folder))

    # Delete zipped file
    local_path.unlink()


def get_available_datasets() -> List[str]:
    """
        Returns a list of all available datasets as a list of their identifying names.
        To get more information on a specific dataset,  refer to the homepage of the
        '`Graph Layout Benchmark Datasets <https://visdunneright.github.io/gd_benchmark_sets/>`_'
        project.

        Example:

        >>> available_datasets = get_available_datasets()
        >>> print(available_datasets)
        ['subways', 'code', 'rome', 'chess', 'steinlib', ...

    :return: List of available dataset names
    :rtype: List[str]
    """
    return list(_get_available_datasets().keys())


def get_available_graph_names(dataset: str) -> List[str]:
    """
    Returns a list of all graphs available in the given dataset.
    Use :func:`get_available_datasets()` to obtain a list of available datasets.

    :param dataset: Name of the dataset
    :type dataset: str
    :return: List of available graphs
    :rtype: List[str]
    """
    _ensure_dataset_downloaded(dataset)
    sub_folder = _get_data_dir() / dataset

    for file in sub_folder.glob("**/*.json"):
        yield file.stem


def iterate_dataset(
    dataset: str, adapt_attributes: bool = True
) -> Iterator[Tuple[str, nx.Graph]]:
    """
    Generates an iterator of all graphs in the specified data set.

    Example:

    >>> for name, g in iterate_dataset('subways'):
    >>>     print("'{name}' has {n} vertices and {m} edges".format(name=name, n=g.order(), m=len(g.edges()))


    In order to obtain a list of all available dataset names call :func:`get_available_datasets`.

    :param dataset: name of the dataset.
    :type dataset: str
    :param adapt_attributes: If true, "weight", "x" and "y" are converted to float (if present),
                             and a "pos" attribute is calculated from "x" and "y"
    :type adapt_attributes: bool
    :return: Iterator over all graphs of the dataset and its name
    :rtype: Iterator[Tuple[str, Graph]]
    """
    _ensure_dataset_downloaded(dataset)
    sub_folder = _get_data_dir() / dataset

    for file in sub_folder.glob("**/*.json"):
        with open(file, encoding="utf-8") as f:
            graph = json.load(f)
        yield file.stem, _get_graph(graph, adapt_attributes)


def _get_graph(json_load: Any, adapt_attributes: bool) -> nx.Graph:
    graph = nx.node_link_graph(json_load)

    if adapt_attributes:

        def _convert_edge_to_float(parameter: str):
            for edge, to_convert in nx.get_edge_attributes(graph, parameter).items():
                try:
                    if isinstance(to_convert, str):
                        graph.edges[edge][parameter] = (
                            0 if to_convert == "" else float(to_convert)
                        )
                except ValueError:
                    pass

        def _convert_node_to_float(parameter: str):
            for node, to_convert in nx.get_node_attributes(graph, parameter).items():
                try:
                    if isinstance(to_convert, str):
                        graph.nodes[node][parameter] = (
                            0 if to_convert == "" else float(to_convert)
                        )
                except ValueError:
                    pass

        # Networkx cannot handle weights and positions that are not numerical
        # So we take care of it here by converting them to float
        _convert_edge_to_float("weight")
        _convert_node_to_float("weight")
        _convert_node_to_float("x")
        _convert_node_to_float("y")

        # If the nodes have x and y values, create a pos attribute, which networkx can work with
        x = nx.get_node_attributes(graph, "x")
        y = nx.get_node_attributes(graph, "y")
        pos = nx.get_node_attributes(graph, "pos")

        if len(x) > 0 and len(y) > 0 and len(pos) == 0:
            try:
                pos = {
                    key: [float(x_value), float(y[key])] for key, x_value in x.items()
                }
                nx.set_node_attributes(graph, pos, "pos")
            except ValueError:
                pass
        elif len(pos) > 0:
            try:
                pos = {
                    key: [float(x) for x in pos_value.strip('"').split(",")]
                    for key, pos_value in pos.items()
                }
                nx.set_node_attributes(graph, pos, "pos")
            except ValueError:
                pass

    return graph


def get_specific_graph(
    dataset: str, graph_name: str, adapt_attributes: bool = True
) -> nx.Graph:
    """
    Use this function if you only want to retrieve a single graph from a dataset
    instead of iterating over the whole dataset using :func:`iterate_dataset()`.

    **Note**: Do not use this function to iterate over the whole dataset. You might run
    into a '429 Too Many Requests' HTTP Error, as the connection to OSF is reestablished
    on each call.

    :param dataset: Name of the dataset
    :type dataset: str
    :param graph_name: Name of the graph in the dataset
    :type graph_name: str
    :param adapt_attributes: If true, "weight", "x" and "y" are converted to float (if present),
                             and a "pos" attribute is calculated from "x" and "y"
    :type adapt_attributes: bool
    :return: The graph in question as a networkX graph
    :rtype: nx.Graph
    :raises ValueError: if the given graph is not available in the dataset
    """
    _ensure_dataset_downloaded(dataset)
    sub_folder = _get_data_dir() / dataset

    graph = None
    for file in sub_folder.glob(f"**/{graph_name}.json"):
        with open(file, encoding="utf-8") as f:
            graph = json.load(f)
        break

    if graph is None:
        raise KeyError(
            f"The graph '{graph_name}' is not available in the dataset '{dataset}'"
        )

    return _get_graph(graph, adapt_attributes)
