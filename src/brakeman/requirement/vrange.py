from __future__ import annotations
from typing import Any


class VRange(object):
    """
    Represent a version range, default [a, b)
    """
    def __init__(self, start: Any = None, end: Any = None, include_start: bool = True, include_end: bool = False) -> None:
        self.set_values(start, end, include_start, include_end)

    def set_values(self, start: Any = None, end: Any = None, include_start: bool = True, include_end: bool = False) -> None:
        self.start = start
        self.end = end
        self.include_start = include_start
        self.include_end = include_end

    def gt(self, value: Any) -> VRange:
        """
        set range (value, +infinity)
        """
        self.set_values(value, include_start=False)
        return self

    def ge(self, value: Any) -> VRange:
        """
        Set range [value, +infinity)
        """
        self.set_values(value)
        return self

    def le(self, value: Any) -> VRange:
        """
        Set range (-infinity, value]
        """
        self.set_values(end=value, include_end=True)
        return self

    def lt(self, value: Any) -> VRange:
        """
        Set range (-infinity, value)
        """
        self.set_values(end=value)
        return self

    def open(self, start=None, end=None) -> VRange:
        self.set_values(start, end, include_start=False, include_end=False)
        return self

    def close(self, start, end) -> VRange:
        self.set_values(start, end, include_start=True, include_end=True)
        return self

    def left_open(self, start, end) -> VRange:
        self.set_values(start, end, include_start=False, include_end=True)
        return self

    def right_open(self, start, end) -> VRange:
        self.set_values(start, end, include_start=True, include_end=False)
        return self

    def overlap(self, other) -> bool:
        if not isinstance(other, VRange):
            raise ValueError(f"'{other}' is not a class of {self.__class__.__name__}")
        p_start, p_end = -1, 1
        if self.start is not None:
            p_start = other.relative_p(self.start)
            if p_start == 0 and self.start == other.end:
                return self.include_start
        if self.end is not None:
            p_end = other.relative_p(self.end)
            if p_end == 0 and self.end == other.start:
                return self.include_end
        return p_start == 0 or p_end == 0 or p_start + p_end == 0

    def relative_p(self, value: Any) -> int:
        """
        Relative position of a value in the range:
        -1 [ 0 ] 1
        """
        if self.start is not None:
            if value < self.start or (value == self.start and not self.include_start):
                return -1
        if self.end is not None:
            if value > self.end or (value == self.end and not self.include_end):
                return 1
        return 0

    def in_range(self, value: Any) -> bool:
        """
        Check a value in the range
        """
        return self.relative_p(value) == 0

    def __str__(self) -> str:
        """
        Return: [/(start, end)/]
        """
        left = '[' if self.include_start and self.start is not None else '('
        right = ']' if self.include_end and self.end is not None else ')'

        start = str(self.start) if self.start  is not None else '-Inf'
        end = str(self.end) if self.end is not None else '+Inf'

        return f"{left}{start}, {end}{right}"

    def __repr__(self) -> str:
        return f"Range: {self}"
