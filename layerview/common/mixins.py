"""Common mixins."""

from abc import ABC, abstractmethod


class MixinMarkdown(ABC):
    @abstractmethod
    def as_markdown(self) -> str:
        """Return Markdown string representation for this object.

        Returns
        -------
        str
            Markdown string representation for this object.
        """
        pass
