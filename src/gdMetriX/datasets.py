# gdMetriX
#
# Copyright (C) 2024  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
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

The project aims to collect datasets used for graph layout algorithms and make them available for long-term access.
The graphs are stored on the `Open Science Foundation platform <https://osf.io/j7ucv/>`_

Information about the individual datasets can be found at the
`project homepage <https://visdunneright.github.io/gd_benchmark_sets/>`_. For more information refer to the
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

The module takes care of downloading, caching, maintaining and updating the graphs automatically. In case there are
any problems or you want to free up disc space, you can clean all saved data with the following command:

.. code-block:: python

    >>> clear_cache()

Methods
-------
"""
import json
import os
import shutil
import sys
import tarfile
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import List, Iterator, Tuple

import networkx as nx
import osfclient
from osfclient import cli


def __get_data_dir__():
    # Windows
    if sys.platform.startswith("win"):
        os_path = getenv("TEMP")
    # Darwin
    elif sys.platform.startswith("darwin"):
        os_path = "~/Library/Application Support"
    # Linux/Unix
    else:
        os_path = getenv("XDG_DATA_HOME", "~/.local/share")

    path = Path(os_path) / "GDMetrics/"

    return path.expanduser()


class _Args:
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
        # remove argument:
        self.target = target
        # clone argument:
        self.output = output
        # fetch arguments:
        self.remote = remote
        self.local = local


def __get_default_arguments():
    return _Args(
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


def __get_project__():
    osf = osfclient.OSF()
    return osf.project("j7ucv")


def __get_available_files_from_server__(proj):
    available_files = []

    for x in proj.storage().folders:
        if x.name == "nx_json":
            for y in x.files:
                available_files.append(y)
            break

    return available_files


def __save_available_files_to_disk__(filename: Path, available_files):
    with filename.open("w") as f:
        json.dump(available_files, f)


def __get_available_files_from_disk__(filename: Path):
    with filename.open() as f:
        return json.load(f)


def clear_cache() -> None:
    """
    In case that there any issues with corrupted data, call this method to clear all graphs saved to the disk.
    """
    shutil.rmtree(__get_data_dir__())


def __get_available_datasets__():
    filename = __get_data_dir__() / "available_datasets.json"

    filename.parent.mkdir(exist_ok=True)

    available_files = None

    def __newer_version_exists__() -> bool:
        try:
            project = __get_project__()
        except:
            # If we cannot even obtain the project info we are unlikely to re-download it -> return False to be save
            return False

        last_modified = datetime.strptime(
            project.date_modified.split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )

        try:
            json_data = __get_available_files_from_disk__(filename)
            last_downloaded = datetime.strptime(
                json_data["created"], "%Y-%m-%dT%H:%M:%S"
            )
        except:
            # If we cannot obtain the info from the disk, we assume something is fishy -> re-download to be save
            return True

        return last_modified > last_downloaded

    # Try to get the list of available files from the .json
    if filename.exists():
        if __newer_version_exists__():
            # Delete everything to trigger a re-download
            clear_cache()
        else:
            available_files = __get_available_files_from_disk__(filename)["files"]

    # Otherwise try to download them from OSF
    if available_files is None:
        proj = __get_project__()
        available_files = [
            filedata.path for filedata in __get_available_files_from_server__(proj)
        ]

        # Save data to disk
        __save_available_files_to_disk__(
            filename,
            {
                "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "files": available_files,
            },
        )

    dic = {}
    for file in available_files:
        dic[os.path.basename(file).split(".")[0]] = file
    return dic


def __ensure_dataset_downloaded__(name: str) -> None:
    all_files = __get_available_datasets__()
    remote_path = all_files[name]
    sub_folder = __get_data_dir__() / name
    local_path = __get_data_dir__() / (name + ".tar.gz")

    # If the sub_folder already exists, we assume that everything is already downloaded
    if sub_folder.exists() and len(os.listdir(sub_folder)) > 0:
        return

    sub_folder.mkdir(parents=True, exist_ok=True)

    # Download the zipped directory
    arguments = __get_default_arguments()
    arguments.remote = remote_path
    arguments.local = local_path
    arguments.force = True
    cli.fetch(arguments)

    # Unzip
    tar = tarfile.open(str(local_path), "r:gz")
    tar.extractall(path=str(sub_folder))
    tar.close()

    # Delete zipped file
    local_path.unlink()


def get_available_datasets() -> List[str]:
    """
        Returns a list of all available datasets as a list of their identifying names. To get more information on a
        specific dataset,  refer to the homepage of the
        '`Graph Layout Benchmark Datasets <https://visdunneright.github.io/gd_benchmark_sets/>`_' project.

        Example:

        >>> available_datasets = get_available_datasets()
        >>> print(available_datasets)
        ['subways', 'code', 'rome', 'chess', 'steinlib', ...

    :return: List of available dataset names
    :rtype: List[str]
    """
    return list(__get_available_datasets__().keys())


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
    :param adapt_attributes: If true, "weight", "x" and "y" are converted to float (if present), and a "pos" attribute
                             is calculated from "x" and "y"
    :type adapt_attributes: bool
    :return: Iterator over all graphs of the dataset and its name
    :rtype: Iterator[Tuple[str, Graph]]
    """
    __ensure_dataset_downloaded__(dataset)
    sub_folder = __get_data_dir__() / dataset

    for file in sub_folder.glob("**/*.json"):
        with open(file) as f:
            graph = json.load(f)

        graph = nx.node_link_graph(graph)

        if adapt_attributes:

            def _convert_to_float(parameter: str):
                for edge, to_convert in nx.get_edge_attributes(
                    graph, parameter
                ).items():
                    try:
                        graph.edges[edge][parameter] = float(to_convert)
                    except ValueError:
                        pass

            # Networkx cannot handle weights and positions that are not numerical
            # So we take care of it here by converting them to float
            _convert_to_float("weight")
            _convert_to_float("x")
            _convert_to_float("y")

            # If the nodes have x and y values, create a pos attribute, which networkx can work with
            x = nx.get_node_attributes(graph, "x")
            y = nx.get_node_attributes(graph, "y")
            pos = nx.get_node_attributes(graph, "pos")

            if len(x) > 0 and len(y) > 0 and len(pos) == 0:
                try:
                    pos = {
                        key: [float(x_value), float(y[key])]
                        for key, x_value in x.items()
                    }
                    nx.set_node_attributes(graph, pos, "pos")
                except ValueError:
                    pass

        yield file.stem, graph
