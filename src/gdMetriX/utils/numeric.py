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
Gathers some common helper functions for numeric evaluations.
"""

from gdMetriX.common import Numeric

import math

PRECISION = 1e-09


def set_precision(precision: float) -> None:
    """
        Sets the global precision used for all calculation. Any two numbers with a difference smaller than `precision`
         are considered as equal
    :param precision: Precision
    :type precision: float
    """
    global PRECISION
    PRECISION = precision


def get_precision() -> float:
    """
        Returns the current precision value
    :return: Precision
    :rtype: float
    """
    global PRECISION
    return PRECISION


def greater_than(a: Numeric, b: Numeric) -> bool:
    """
    Checks if a is greater than b within the previously specified precision.
    :param a: First numeric
    :type a: Numeric
    :param b: Second numeric
    :type b: Numeric
    :return: True if and only if the two numbers are equal within the specified precision.
    :rtype: bool
    """
    if numeric_eq(a, b):
        return False

    return a > b


def numeric_eq(a: Numeric, b: Numeric) -> bool:
    """
    Checks if two numerics are equal within the previously specified precision.
    :param a: First numeric
    :type a: Numeric
    :param b: Second numeric
    :type b: Numeric
    :return: True if and only if the two numbers are equal within the specified precision.
    :rtype: bool
    """
    return math.isclose(a, b, abs_tol=PRECISION)
