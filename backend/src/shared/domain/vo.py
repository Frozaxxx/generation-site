import abc
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValueObject(abc.ABC):  # noqa: B024
    """
    Базовый класс для объекта значения, идентичность определяется комбинацией полей.
    """
