"""Markdown loading utilities."""
import re
from pathlib import Path
from typing import List, Union


class MarkdownLoader:
    """Markdown document loading abstraction layer."""

    _PATTERN_IMG: re.Pattern = re.compile(pattern=r"(!\[.*\]\()(.+)(\))")
    _NTFS_ABS_PATH: re.Pattern = re.compile(
        pattern=r"^[a-zA-Z]:\\(((?![<>:\"\/\\|?*]).)+((?<![ .])\\)?)*$"
    )
    _UNIX_ABS_PATH: re.Pattern = re.compile(pattern=r"^(?:/[^/\n]+)*$")

    @staticmethod
    def load(path: Union[str, Path]) -> str:
        """Load Markdown document.

        Also converts relative paths to absolute.

        Parameters
        ----------
        path : Union[str, Path]

        Returns
        -------
        str
            Loaded and sanitized Markdown file content.
        """
        path_md: Path = Path(path).absolute()

        with open(path_md, "r") as file:
            text = file.read()

        processed = MarkdownLoader._handle_img_paths(
            md=text, md_parent_dir=path_md.parent
        )

        return processed

    @staticmethod
    def _handle_img_paths(md: str, md_parent_dir: Path) -> str:
        """Make relative Markdown image paths absolute.

        Parameters
        ----------
        md : str
            Markdown document to process.
        md_parent_dir : Path
            Parent dir of the processed Markdown document.

        Returns
        -------
        str
            Markdown text with relative image paths converted to absolute.
        """
        matches = []
        last_match = MarkdownLoader._PATTERN_IMG.search(string=md)
        while last_match:
            matches.append(last_match)
            new_match = MarkdownLoader._PATTERN_IMG.search(
                string=md, pos=last_match.end()
            )
            last_match = new_match

        chunks: List[str] = []
        last_end: int = 0
        for match in matches:
            start, end = match.regs[0]

            # From last match end, to before current match.
            chunks.append(md[last_end:start])

            # Matched groups
            chunks.append(match.group(1))
            # Make image path absolute
            field_img_path = match.group(2)
            if MarkdownLoader._UNIX_ABS_PATH.match(
                field_img_path
            ) or MarkdownLoader._UNIX_ABS_PATH.match(field_img_path):
                chunks.append(field_img_path)
            else:
                img_uri: str = (md_parent_dir / Path(field_img_path)).as_uri()
                chunks.append(img_uri)

            chunks.append(match.group(3))

            last_end = end

        chunks.append(md[last_end:])

        fixed_text: str = "".join(chunks)
        return fixed_text
