"""The base class of EventGraph components."""
from abc import ABC, abstractmethod
import json


class Base(ABC):
    """Base class of components."""

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs):
        """Create an object from language analysis."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, *args, **kwargs):
        """Create an object from a dictionary."""
        pass

    @abstractmethod
    def finalize(self):
        """Finalize this object."""
        pass

    @abstractmethod
    def to_dict(self):
        """Convert this object into a dictionary."""
        pass

    def __repr__(self):
        """Print this object."""
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
