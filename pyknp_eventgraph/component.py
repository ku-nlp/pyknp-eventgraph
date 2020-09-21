"""The base class of EventGraph components."""
from abc import ABC, abstractmethod


class Component(ABC):
    """The base of EventGraph components."""

    def __repr__(self) -> str:
        return self.to_string()

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        raise NotImplementedError

    @abstractmethod
    def to_string(self) -> str:
        """Convert this object into a string."""
        raise NotImplementedError
