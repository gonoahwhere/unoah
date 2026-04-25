from wx import (
    Colour,
    Cursor,
    CURSOR_HAND,
    EVT_BUTTON,
    EVT_SIZE,
    Font,
    Point,
    Panel as WxPanel,
    Size,
    SizeEvent,
    StaticBitmap,
    StaticText,
)
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from wx.lib import buttons

from ..utils.config import Config
from ..utils.util import make_bitmap_clickable

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from ..game import Game

class Panel(ABC):
    """A game panel."""

    __slots__: tuple[str, ...] = ('panel', 'game', 'theme_toggle_icon')

    panel: WxPanel
    """The panel's inner wxWidgets panel."""

    game: Game
    """The parent game instance."""

    theme_toggle_icon: StaticBitmap
    """The panel's theme toggle icon."""

    def __init__(self, game: Game, *, primary: bool = False):
        self.panel = WxPanel(game.window)
        self.panel.SetBackgroundColour(game.config.get_colour('bg_primary'))

        self.game = game

        self.theme_toggle_icon = StaticBitmap(self.panel, bitmap=game.config.toggle_image)
        make_bitmap_clickable(self.theme_toggle_icon, game.flip_theme)

        self.panel.Bind(EVT_SIZE, self._on_resize)

        if primary:
            self.game.current_panel = self
        else:
            self.panel.Hide()

    def _on_resize(self, event: SizeEvent) -> None:
        """Handles a resize event."""

        window_boundaries = self.panel.GetClientSize()
        toggle_boundaries = self.theme_toggle_icon.GetSize()

        self.theme_toggle_icon.SetPosition(Point(window_boundaries.width - toggle_boundaries.width - 10, 10))

        event.Skip()

    def reflect_button_theme(self, button: buttons.GenButton) -> None:
        """Reflects a button based on the game's theme."""

        button.SetBackgroundColour(self.game.config.get_colour('button_bg'))
        button.SetForegroundColour(self.game.config.get_colour('button_text'))

    @abstractmethod
    def reflect_theme(self) -> None:
        """Reflects the panel based on the game's theme."""

        self.panel.SetBackgroundColour(self.game.config.get_colour('bg_primary'))

        self.theme_toggle_icon.SetBitmap(self.game.config.toggle_image)

    @abstractmethod
    def restore(self) -> None:
        """Restores the panel back."""

        self.game.current_panel = self
        self.panel.Show()

    @abstractmethod
    def cleanup(self) -> None:
        """Runs at the end of the panel's lifecycle."""

        pass

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

        button.SetBackgroundColour(self.game.config.get_colour('button_bg'))
        button.SetForegroundColour(self.game.config.get_colour('text_primary'))
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
        text.SetForegroundColour(colour or self.game.config.get_colour('text_primary'))

        return text