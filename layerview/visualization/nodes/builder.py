"""Node builder base."""
from abc import ABC, abstractmethod

from panda3d.core import NodePath


class NodeBuilder(ABC):
    @staticmethod
    @abstractmethod
    def build_node(*args, **kwargs) -> NodePath:
        """Build node."""
        pass
