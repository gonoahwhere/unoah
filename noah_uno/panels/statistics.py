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

from .panel import Panel
from ..utils.scores import load_scores
from ..utils.util import safe_add_to_sizer

if TYPE_CHECKING:
    from wx import SizeEvent, StaticText
    from ..game import Game

class Statistics(Panel):
    """A statistics panel."""

    __slots__: tuple[str, ...] = ('heading', 'lines', 'main_menu_button')

    heading: StaticText
    """The statistics panel's heading."""

    lines: tuple[StaticText, ...]
    """The statistics panel's lines."""

    main_menu_button: buttons.GenButton
    """The statistics panel's main menu button."""

    def __init__(self, game: Game):
        super().__init__(game)

        self.heading = self.new_text('UNOAH Scoreboard', 64)

        self.lines = (
            self.new_text('Player', 28),
            self.new_text('0', 28),
            self.new_text('Opponent', 28),
            self.new_text('0', 28),
        )

        self.main_menu_button = self.new_button('MAIN MENU', lambda: game.open('main_menu'))

    def reflect_theme(self) -> None:
        """Reflects the panel based on the game's theme."""

        self.heading.SetForegroundColour(self.game.config.get_colour('text_primary'))

        for line in self.lines:
            line.SetForegroundColour(self.game.config.get_colour('text_primary'))

        self.reflect_button_theme(self.main_menu_button)

        super().reflect_theme()

    def restore(self) -> None:
        """Restores the statistics panel."""

        # REFRESH COUNTS FROM DISK EACH TIME IT'S OPENED
        scores = load_scores()

        self.lines[1].SetLabel(str(scores.get('player_wins', 0)))
        self.lines[3].SetLabel(str(scores.get('opponent_wins', 0)))

        main_sizer = BoxSizer(VERTICAL)
        line_sizer = FlexGridSizer(cols=2, rows=2, gap=Size(50, 20))

        main_sizer.AddStretchSpacer()
        safe_add_to_sizer(main_sizer, self.heading, 0, ALIGN_CENTER, 20)
        main_sizer.AddSpacer(60)

        lines = iter(self.lines)

        for _ in range(2):
            safe_add_to_sizer(line_sizer, next(lines), 0, ALIGN_CENTER_VERTICAL | ALIGN_RIGHT)
            safe_add_to_sizer(line_sizer, next(lines), 1, EXPAND)

        main_sizer.Add(line_sizer, 0, ALIGN_CENTER)
        main_sizer.AddSpacer(100)

        safe_add_to_sizer(main_sizer, self.main_menu_button, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)

        super().restore()

    def cleanup(self) -> None:
        """Runs at the end of the statistics panel's lifecycle."""

        super().cleanup()