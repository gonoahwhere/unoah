from wx import ALIGN_CENTER, ALL, BoxSizer, HORIZONTAL, ID_OK, Size, VERTICAL
from typing import TYPE_CHECKING

from .dialog import Dialog

if TYPE_CHECKING:
    from ..panels.session import Session

TITLE = 'Draw 4 Incoming'
"""The title of the draw 4 challenge dialog."""

class Draw4Challenge(Dialog):
    """A dialog that asks the player whether to challenge the opponent's DRAW4."""

    __slots__: tuple[str, ...] = ('challenged',)

    challenged: bool
    """Whether the player chose to challenge."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, TITLE, Size(700, 400))

        self.challenged = False

        main_sizer = BoxSizer(HORIZONTAL)
        main_sizer.AddStretchSpacer()

        sizer = BoxSizer(VERTICAL)

        subtitle = self.new_text('The opponent is about to play a draw 4.', 16)
        sizer.Add(subtitle, 0, ALIGN_CENTER)
        sizer.AddSpacer(10)

        title = self.new_text('Do you want to challenge it?', 24)
        sizer.Add(title, 0, ALIGN_CENTER)

        button_sizer = BoxSizer(HORIZONTAL)

        challenge_button = self.new_button('YES', lambda: self.complete(True))
        accept_button = self.new_button('NO', lambda: self.complete(False))

        button_sizer.Add(challenge_button, 0, ALL, 20)
        button_sizer.Add(accept_button, 0, ALL, 20)

        sizer.AddSpacer(40)
        sizer.Add(button_sizer, 0, ALIGN_CENTER)
        sizer.AddSpacer(10)

        note = self.new_text('Not challenging allows you to stack it.', 16)
        sizer.Add(note, 0, ALIGN_CENTER)

        main_sizer.Add(sizer, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)

    def complete(self, challenged: bool) -> None:
        """Completes the dialog."""

        self.challenged = challenged
        self.EndModal(ID_OK)