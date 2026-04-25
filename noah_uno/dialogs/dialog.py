from wx import (
    CAPTION,
    Colour,
    Cursor,
    CURSOR_HAND,
    Dialog as WxDialog,
    EVT_BUTTON,
    Font,
    Panel as WxPanel,
    Size,
    StaticText,
)
from typing import TYPE_CHECKING
from wx.lib import buttons

from ..utils.config import Config
from ..panels.panel import Panel

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

class Dialog(WxDialog):
    """A modal dialog."""

    __slots__: tuple[str, ...] = ('panel', 'parent')

    panel: WxPanel
    """The dialog's inner wxWidgets panel."""

    parent: Panel
    """The dialog's parent panel."""

    def __init__(self, panel: Panel, title: str, size: Size, *, style: int = 0):
        super().__init__(panel.panel, style=CAPTION | style)

        self.SetTitle(title)
        self.SetSize(size)
        self.CenterOnScreen()

        self.panel = WxPanel(self)
        self.panel.SetBackgroundColour(panel.game.config.get_colour('bg_primary'))

        self.parent = panel

    def new_button(
        self,
        label: str,
        callback: Callable[[], Any],
        size: Size | None = None,
        font: Font | None = None,
        can_focus: bool = False,
        use_focus_indicator: bool = False,
    ) -> buttons.GenButton:
        """Creates a new button based on the game's configuration."""

        button = buttons.GenButton(self.panel, label=label)

        button.SetBackgroundColour(self.parent.game.config.get_colour('button_bg'))
        button.SetForegroundColour(self.parent.game.config.get_colour('text_primary'))
        button.SetFont(font or Config.new_font(28))
        button.SetCanFocus(can_focus)
        button.SetUseFocusIndicator(use_focus_indicator)
        button.SetMinSize(size or Size(225, 65))
        button.SetCursor(Cursor(CURSOR_HAND))
        button.Bind(EVT_BUTTON, lambda _: callback())

        return button

    def new_text(self, label: str, font_size: int, *, colour: Colour | None = None) -> StaticText:
        """Creates a new text based on the game's configuration."""

        text = StaticText(self.panel, label=label)
        text.SetFont(Config.new_font(font_size))
        text.SetForegroundColour(colour or self.parent.game.config.get_colour('text_primary'))

        return text