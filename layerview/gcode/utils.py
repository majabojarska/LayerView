"""Misc. utilities."""

from typing import List


def str_to_chars(text: str) -> List[str]:
    """Convert str to list of characters.

    Parameters
    ----------
    text : str
        String to convert to a list of characters.

    Returns
    -------
    List[str]
        List of characters in provided str.
    """
    return [*text]
