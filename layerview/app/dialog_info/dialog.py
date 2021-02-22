from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PyQt5.QtWidgets import QDialog

from layerview.app.pyuic.dialog_info import Ui_Dialog
from layerview.common.markdown import MarkdownLoader


class InfoDialog(QDialog):
    def __init__(
        self,
        title: str,
        markdown: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle(title)
        self.ui.textEdit.setMarkdown(markdown)

        if width:
            self.setMinimumWidth(width)
        if height:
            self.setMinimumHeight(height)

    @staticmethod
    def from_md_file(
        title: str,
        path_md: Union[Path, str],
        width: Optional[int] = None,
        height: Optional[int] = None,
        *args,
        **kwargs,
    ) -> InfoDialog:
        dialog: InfoDialog = InfoDialog(
            title=title,
            markdown=MarkdownLoader.load(path_md),
            width=width,
            height=height,
            *args,
            **kwargs,
        )
        return dialog
