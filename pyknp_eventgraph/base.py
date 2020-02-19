"""The base class of EventGraph components."""
from abc import ABC, abstractmethod
import json


class Base(ABC):
    """Base class of components."""

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs):
        """Create an instance from language analysis."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, *args, **kwargs):
        """Create an instance from a dictionary."""
        pass

    @abstractmethod
    def finalize(self):
        """Finalize this instance."""
        pass

    @abstractmethod
    def to_dict(self):
        """Convert this instance into a dictionary."""
        pass

    def __repr__(self):
        """Print this instance."""
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
