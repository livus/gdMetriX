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

import contextlib
import functools
import inspect
import math
from typing import Callable, Generator

from gdMetriX.common import Numeric

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


@contextlib.contextmanager
def precision_context(precision: float) -> Generator[None, None, None]:
    """
    Sets the global precision for the duration of a ``with`` block, and restores the previous one
    afterwards - also when the block raises.

    Example:

    .. code-block:: python

        with precision_context(1e-6):
            ...  # all comparisons use 1e-6 here
        # and the previous precision again here

    :param precision: Precision to use within the block
    :type precision: float
    """
    previous = get_precision()
    set_precision(precision)
    try:
        yield
    finally:
        set_precision(previous)


def applies_precision(func: Callable) -> Callable:
    """
    Decorates a function taking a ``precision`` argument, so that the global precision is set to
    that argument for the duration of the call - wherever the function compares numbers, including
    in what it does with the results of the functions it calls - and restored afterwards.

    Without it, a call with a coarse precision would leak it into every later computation.

    :param func: A function with a ``precision`` parameter
    :type func: Callable
    :return: The decorated function
    :rtype: Callable
    """
    parameters = list(inspect.signature(func).parameters.values())
    names = [parameter.name for parameter in parameters]

    if "precision" not in names:
        raise TypeError(f"'{func.__name__}' has no 'precision' parameter")

    index = names.index("precision")
    default = parameters[index].default

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if index < len(args):
            precision = args[index]
        else:
            precision = kwargs.get("precision", default)

        if precision is inspect.Parameter.empty:
            # Not given and without a default: let the call fail as it would undecorated
            return func(*args, **kwargs)

        with precision_context(precision):
            return func(*args, **kwargs)

    return wrapper


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
    # numeric_eq(a, b), inlined: this runs millions of times during crossing detection
    if math.isclose(a, b, abs_tol=PRECISION):
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
