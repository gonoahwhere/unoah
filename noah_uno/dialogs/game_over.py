from wx import (
    ALIGN_CENTER,
    ALL,
    BoxSizer,
    HORIZONTAL,
    ID_OK,
    Size,
    VERTICAL,
)
from typing import TYPE_CHECKING
from sys import platform

from .dialog import Dialog

if TYPE_CHECKING:
    from ..panels.session import Session

class GameOver(Dialog):
    """A dialog that shows when a game session ends."""

    __slots__: tuple[str, ...] = ('session',)

    session: Session
    """The parent game session instance."""

    def __init__(self, session: Session, *, player_won: bool) -> None:
        super().__init__(session, 'Congratulations' if player_won else 'Game Over', Size(800 if platform.startswith('win') else 600, 300),)

        self.session = session

        session.game_over = True
        session.game.player.play('win' if player_won else 'loss')

        main_sizer = BoxSizer(HORIZONTAL)
        main_sizer.AddStretchSpacer()

        sizer = BoxSizer(VERTICAL)

        title = self.new_text(f'You {"beat" if player_won else "were beaten by"} the opponent!', 28,)

        sizer.Add(title, 0, ALIGN_CENTER, 8)
        sizer.AddSpacer(40)

        button_sizer = BoxSizer(HORIZONTAL)

        play_again_button = self.new_button('PLAY AGAIN', lambda: self.complete(True))
        main_menu_button = self.new_button('MAIN MENU', lambda: self.complete(False))

        button_sizer.Add(play_again_button, 0, ALL, 20)
        button_sizer.Add(main_menu_button, 0, ALL, 20)

        sizer.Add(button_sizer, 0, ALIGN_CENTER, 8)

        main_sizer.Add(sizer, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)

    def complete(self, play_again: bool) -> None:
        """Completes the dialog."""

        self.EndModal(ID_OK)

        self.session.game.open('session' if play_again else 'main_menu')