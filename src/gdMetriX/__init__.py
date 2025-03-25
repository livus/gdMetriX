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
__init__.py
"""

from gdMetriX.boundary import (
    area,
    area_tight,
    aspect_ratio,
    bounding_box,
    height,
    normalize_positions,
    width,
)
from gdMetriX.common import get_node_positions, Vector, Angle, euclidean_distance
from gdMetriX.crossings import (
    crossing_angles,
    crossing_angular_resolution,
    crossing_density,
    get_crossings,
    get_crossings_quadratic,
    number_of_crossings,
    planarize,
)
from gdMetriX.datasets import clear_cache, get_available_datasets, iterate_dataset
from gdMetriX.distribution import (
    center_of_mass,
    closest_pair_of_elements,
    closest_pair_of_points,
    concentration,
    gabriel_ratio,
    heatmap,
    homogeneity,
    horizontal_balance,
    node_orthogonality,
    vertical_balance,
    smallest_enclosing_circle,
)
from gdMetriX.edge_directions import (
    angular_resolution,
    average_flow,
    coherence_to_average_flow,
    combinatorial_embedding,
    edge_angles,
    edge_length_deviation,
    edge_orthogonality,
    minimum_angle,
    ordered_neighborhood,
    upwards_flow,
)
from gdMetriX.symmetry import (
    SymmetryType,
    edge_based_symmetry,
    reflective_symmetry,
    visual_symmetry,
    stress,
    even_neighborhood_distribution,
)

__version__ = "0.0.4"
