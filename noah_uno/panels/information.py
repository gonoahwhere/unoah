from wx import (
    ALIGN_CENTER,
    ALIGN_CENTER_VERTICAL,
    ALIGN_RIGHT,
    BoxSizer,
    EXPAND,
    FlexGridSizer,
    Size,
    VERTICAL,
)
from typing import TYPE_CHECKING
from wx.lib import buttons
from sys import platform

from .panel import Panel
from ..utils.util import safe_add_to_sizer

if TYPE_CHECKING:
    from wx import SizeEvent, StaticText
    from ..game import Game

INFORMATION: dict[str, str] = {
    'Objective': 'Be the first player to clear out all of your cards.',
    'Taking a turn': 'Play a card that matches the middle card by colour or value.',
    'Wild': 'Lets you pick what the next colour should be. Can be played on any card.',
    'Draw 2': 'Forces your opponent to do the same or draw two cards.',
    'Draw 4': 'Forces your opponent to do the same or draw four cards.',
    'Skip': "Skips your opponent's turn.",
    'Reverse': "Also skips your opponent's turn.",
    'Challenge': 'If you believe your opponent has another playable card, challenge their draw four!',
    'Force Play': "Drawn a playable card? It's automatically played.",
    '7-0': 'Play a 7 or 0? Swap hands with your opponent.',
    'NOAH': 'Got 2 cards remaining? Shout NOAH!',
}
"""The game's information."""

class Information(Panel):
    """An instruction panel."""

    __slots__: tuple[str, ...] = ('heading', 'lines', 'main_menu_button')

    heading: StaticText
    """The instruction panel's heading."""

    lines: list[StaticText]
    """The instruction panel's lines of text."""

    main_menu_button: buttons.GenButton
    """The instruction panel's main menu button."""

    def __init__(self, game: Game):
        super().__init__(game)

        self.heading = self.new_text('Core Information', 32 if platform.startswith('win') else 48)
        self.lines = []

        line_font_size = 16 if platform.startswith('win') else 28

        for name, description in INFORMATION.items():
            name_text = self.new_text(name, line_font_size)
            description_text = self.new_text(description, line_font_size)

            self.lines.extend((name_text, description_text))

        self.main_menu_button = self.new_button('MAIN MENU', lambda: game.open('main_menu'))

    def reflect_theme(self) -> None:
        """Reflects the panel based on the game's theme."""

        self.heading.SetForegroundColour(self.game.config.get_colour('text_primary'))

        for line in self.lines:
            line.SetForegroundColour(self.game.config.get_colour('text_primary'))

        self.reflect_button_theme(self.main_menu_button)

        super().reflect_theme()

    def restore(self) -> None:
        """Restores the instruction panel back."""

        main_sizer = BoxSizer(VERTICAL)
        line_sizer = FlexGridSizer(cols=2, rows=len(INFORMATION), gap=Size(50, 20))

        main_sizer.AddStretchSpacer()
        safe_add_to_sizer(main_sizer, self.heading, 0, ALIGN_CENTER, 20)
        main_sizer.AddSpacer(30)

        lines = iter(self.lines)

        for _ in range(0, len(INFORMATION)):
            safe_add_to_sizer(line_sizer, next(lines), 0, ALIGN_CENTER_VERTICAL | ALIGN_RIGHT)
            safe_add_to_sizer(line_sizer, next(lines), 1, EXPAND)

        main_sizer.Add(line_sizer, 0, ALIGN_CENTER)
        main_sizer.AddSpacer(100)

        safe_add_to_sizer(main_sizer, self.main_menu_button, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)

        super().restore()

    def cleanup(self) -> None:
        """Runs at the end of the instruction panel's lifecycle."""

        super().cleanup()