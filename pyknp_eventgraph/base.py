from abc import ABC, abstractmethod
import json


class Base(ABC):
    """Base class of components."""

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs):
        """Build this instance."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, *args, **kwargs):
        """Load this instance."""
        pass

    @abstractmethod
    def assemble(self):
        """Assemble contents to output."""
        pass

    @abstractmethod
    def to_dict(self):
        """Output this information as a dictionary."""
        pass

    def __repr__(self):
        """Print this instance."""
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)
