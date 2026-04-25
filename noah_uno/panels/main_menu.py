from wx import (
    ALIGN_CENTER,
    ALL,
    BoxSizer,
    HORIZONTAL,
    VERTICAL,
)
from typing import TYPE_CHECKING
from wx.lib import buttons

from .panel import Panel

if TYPE_CHECKING:
    from wx import SizeEvent, StaticText
    from ..game import Game

class MainMenu(Panel):
    """A main menu."""

    __slots__: tuple[str, ...] = (
        'title',
        'subtitle',
        'play_button',
        'information_button',
        'statistics_button',
        'quit_button',
    )

    title: StaticText
    """The main menu's title."""

    subtitle: StaticText
    """The main menu's subtitle."""

    play_button: buttons.GenButton
    """The main menu's play button."""

    information_button: buttons.GenButton
    """The main menu's information button."""

    statistics_button: buttons.GenButton
    """The main menu's statistics button."""

    quit_button: buttons.GenButton
    """The main menu's quit button."""

    def __init__(self, game: Game):
        super().__init__(game, primary=True)

        # TITLE
        self.title = self.new_text(game.config.title, 128)

        # SUBTITLE
        self.subtitle = self.new_text(game.config.subtitle, 24)

        # BUTTONS
        self.play_button = self.new_button('PLAY', lambda: game.open('session'))
        self.information_button = self.new_button('INFORMATION', lambda: game.open('information'))
        self.statistics_button = self.new_button('SCOREBOARD', lambda: game.open('statistics'))
        self.quit_button = self.new_button('QUIT', lambda: game.window.Close())

        # SIZERS
        main_sizer = BoxSizer(VERTICAL)
        main_sizer.AddStretchSpacer()

        main_sizer.AddSpacer(100)
        main_sizer.Add(self.title, 0, ALIGN_CENTER)
        main_sizer.AddSpacer(20)
        main_sizer.Add(self.subtitle, 0, ALIGN_CENTER)
        main_sizer.AddSpacer(50)

        button_sizer = BoxSizer(HORIZONTAL)
        button_sizer.Add(self.play_button, 0, ALL, 20)
        button_sizer.Add(self.information_button, 0, ALL, 20)
        button_sizer.Add(self.statistics_button, 0, ALL, 20)
        button_sizer.Add(self.quit_button, 0, ALL, 20)

        main_sizer.Add(button_sizer, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer(2)

        self.panel.SetSizer(main_sizer)

    def reflect_theme(self) -> None:
        """Reflects the main menu based on the game's theme."""

        self.title.SetForegroundColour(self.game.config.get_colour('text_primary'))
        self.subtitle.SetForegroundColour(self.game.config.get_colour('text_primary'))

        self.reflect_button_theme(self.play_button)
        self.reflect_button_theme(self.information_button)
        self.reflect_button_theme(self.statistics_button)
        self.reflect_button_theme(self.quit_button)

        super().reflect_theme()

    def restore(self) -> None:
        """Restores the main menu's panel back."""

        super().restore()

    def cleanup(self) -> None:
        """Runs at the end of the main menu panel's lifecycle."""

        super().cleanup()