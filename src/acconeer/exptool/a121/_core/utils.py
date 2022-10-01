from __future__ import annotations

import enum
import json
import re
from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

import packaging.version


T = TypeVar("T")

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")

Number = Union[int, float]


class ProxyProperty(Generic[T]):
    """
    A descriptor that reduces boilerplate for accessing a certain property in a component.
    If the proxied property has a doc-string, it will be inherited by this descriptor.

    E.g. This can be used to implement "first-element-shortcuts"


        class Component:
            _attribute: int

            ...

            @property
            def attribute(self) -> int:
                return self._attribute

            @attribute.setter
            def attribute(self, new_value: int):
                self._attribute = new_value

        class Container:
            proxy_attribute = ProxyProperty[Component, int](
                lambda container: container.get_first_component(), Component.attribute
            )

            def get_first_component(self):
                ...

    It's recommended to subclass ProxyProperty to fit each Component-Container combination.
    """

    def __init__(
        self,
        accessor: Callable,
        prop: property,
    ):
        """
        :param accessor: The function to call to recieve an object that has the property "prop".
        :param prop: The property object which to proxy upon.
        """
        self._accessor = accessor
        if not isinstance(prop, property):
            raise TypeError(f'Passed "prop" needs to be a property. Actual type: {type(prop)}')
        self._property = prop

        self.__doc__ = prop.__doc__

    @overload
    def __get__(self, obj: None, objtype: Optional[Type] = ...) -> ProxyProperty[T]:
        ...

    @overload
    def __get__(self, obj: Any, objtype: Optional[Type] = ...) -> T:
        ...

    def __get__(
        self,
        obj: Optional[Any],
        objtype: Optional[Type] = None,
    ) -> Union[T, ProxyProperty[T]]:
        if obj is not None:
            proxee = self._accessor(obj)
            # The reason this needs to be ignored boils down to lack of support for
            # generic descriptors (property is a descriptor) in mypy.
            return self._property.__get__(proxee)  # type: ignore[no-any-return]

        return self

    def __set__(self, obj: Any, value: T) -> None:
        proxee = self._accessor(obj)
        self._property.__set__(proxee, value)


def unextend(structure: list[dict[int, T]]) -> T:
    """'Unexpands' a structure and returns the single element in the structure."""
    try:
        (group,) = structure
        (entry,) = group.values()
        return entry
    except Exception as e:
        raise ValueError(f"Could not unextend the structure {structure}") from e


def _convert_value(value: Number, *, factory: Callable[[Number], T]) -> T:
    try:
        # May raise ValueError if e.g. "value" is a non-int string
        converted_value = factory(value)

        if converted_value != value:
            # E.g. int("3") != "3", int(3.5) != 3.5. is catched here.
            raise ValueError

        return converted_value
    except ValueError:
        raise TypeError(f"{value} cannot be converted with {factory}")


def _check_bounds(
    value: Number,
    lower_bound: Optional[Number] = None,
    upper_bound: Optional[Number] = None,
    inclusive: bool = True,
) -> None:
    """Raises a ValueError if:
    * ``value`` is not in [lower_bound, upper_bound], if inclusive = True
    * ``value`` is not in (lower_bound, upper_bound), if inclusive = False
    """
    exclusive = not inclusive

    boundaries = f"{lower_bound}, {upper_bound}"
    interval = f"({boundaries})" if exclusive else f"[{boundaries}]"
    error = ValueError(f"{value} needs to be in {interval}")

    if lower_bound is not None and (
        (exclusive and value <= lower_bound) or (inclusive and value < lower_bound)
    ):
        raise error

    if upper_bound is not None and (
        (exclusive and value >= upper_bound) or (inclusive and value > upper_bound)
    ):
        raise error


def convert_validate_int(
    value: Union[float, int], max_value: Optional[int] = None, min_value: Optional[int] = None
) -> int:
    """Converts an argument to an int.

    :param value: The argument to be converted and boundary checked
    :param max_value: Maximum value allowed
    :param min_value: Minimum value allowed

    :raises: TypeError if value is a string or a float with decimals
    :raises: ValueError if value does not agree with max_value and min_value
    """
    int_value = _convert_value(value, factory=int)
    _check_bounds(int_value, lower_bound=min_value, upper_bound=max_value, inclusive=True)
    return int_value


def validate_float(
    value: float,
    max_value: Optional[float] = None,
    min_value: Optional[float] = None,
    inclusive: bool = True,
) -> float:
    """Converts an argument to a float.

    :param value: The argument to be converted and boundary checked
    :param max_value: Maximum value allowed
    :param min_value: Minimum value allowed
    :param inclusive:
        Whether the bounds ``max_value`` and ``min_value`` should be considered inclusive.
        E.g. value = 0.0, min_value = 0.0, inclusive = False raises a ValueError.

    :raises: TypeError if value cannot be converted to a float.
    :raises: ValueError if value does not agree with max_value and min_value
    """
    float_value = _convert_value(value, factory=float)
    _check_bounds(float_value, lower_bound=min_value, upper_bound=max_value, inclusive=inclusive)
    return float_value


def is_multiple_of(multiplier: int, product: int) -> bool:
    """Returns True if `product` is a multiple of `multiplier`.
    I.e. checks if `multiplicand` is an integer in the equation

    `multiplicand` * `multiplier` = `product`
    """
    return product >= multiplier and product % multiplier == 0


def is_divisor_of(divisor: int, dividend: int) -> bool:
    """Returns True if `dividend` is divided by `divisor` with no remainder
    I.e. checks that `quotient` is an integer in the equation

    `dividend` / `divisor` = `quotient`
    """
    return is_multiple_of(dividend, divisor)


def map_over_extended_structure(
    func: Callable[[ValueT], T], structure: list[dict[KeyT, ValueT]]
) -> list[dict[KeyT, T]]:
    """Applies a function, `func`, to each element of the extended structure.

    Example:

        structure = [{1: "one"}, {2: "two"}]        # KeyT = int, ValueT = str
        func = str.encode                           # ValueT = str, T = bytes

        # Result
        result = [{1: b"one"}, {2: b"two"}]         # KeyT = int, T = bytes

    """
    return [{k: func(v) for k, v in d.items()} for d in structure]


def iterate_extended_structure(
    structure: list[dict[int, ValueT]]
) -> Iterator[Tuple[int, int, ValueT]]:
    """Iterates over the elements of the extended structure.

    :returns: Iterator of (<group id>, <sensor id>, <element>)
    """

    for group_id, group in enumerate(structure):
        for sensor_id, elem in group.items():
            yield (group_id, sensor_id, elem)


class EntityJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, enum.Enum):
            return obj.name

        return json.JSONEncoder.default(self, obj)


def parse_rss_version(rss_version: str) -> packaging.version.Version:
    pattern = (
        r"a121-v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)"
        r"(?:-(?P<pre_phase>rc)(?P<pre_number>\d+))?"
        r"(?:-(?P<dev_number>\d+)-(?P<dev_commit>g\w+))?"
    )
    match = re.fullmatch(pattern, rss_version)
    if not match:
        raise ValueError("Not a valid RSS version")

    groups = match.groupdict()

    is_prerelease = groups["pre_number"] is not None
    is_devrelease = groups["dev_number"] is not None

    release_segment = ""
    pre_segment = ""
    dev_segment = ""

    if is_devrelease:
        dev_segment = f".dev{groups['dev_number']}+{groups['dev_commit']}"

        if is_prerelease:
            groups["pre_number"] = int(groups["pre_number"]) + 1
        else:
            groups["micro"] = int(groups["micro"]) + 1

    if is_prerelease:
        pre_segment = f"{groups['pre_phase']}{groups['pre_number']}"

    release_segment = f"{groups['major']}.{groups['minor']}.{groups['micro']}"

    version = release_segment + pre_segment + dev_segment
    return packaging.version.Version(version)
