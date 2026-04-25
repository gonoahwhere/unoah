from wx import (
    ALL,
    ALIGN_CENTER,
    BitmapBundle,
    BoxSizer,
    CLOSE_BOX,
    HORIZONTAL,
    ID_OK,
    Size,
    StaticBitmap,
    VERTICAL,
)
from typing import TYPE_CHECKING

from ..utils.card import Card, COLOUR_MAPPING
from .dialog import Dialog
from ..utils.util import make_bitmap_clickable

if TYPE_CHECKING:
    from ..utils.card import Colour
    from ..panels.session import Session

TITLE = 'Wild card selection'
"""The title of the wild card selection dialog."""

class WildCardSelection(Dialog):
    """A wild card selection dialog."""

    __slots__: tuple[str, ...] = ('selected',)

    selected: Colour | None
    """The selected colour."""

    def __init__(self, session: Session, card: Card, *, force: bool = False):
        super().__init__(session, TITLE, Size(600, 300), style=0 if force else CLOSE_BOX)

        self.selected = None
        
        main_sizer = BoxSizer(VERTICAL)
        main_sizer.AddStretchSpacer()

        sizer = BoxSizer(HORIZONTAL)

        title = self.new_text('Which colour are you picking?', 24)
        sizer.Add(title, 0, ALIGN_CENTER)

        selection_sizer = BoxSizer(HORIZONTAL)

        for colour in COLOUR_MAPPING.values():
            display_card = Card(session.game.config, card.key)
            display_card.set_wild_card_colour(colour)

            bitmap = StaticBitmap(self.panel, bitmap=BitmapBundle(display_card.get_image((80, 120))),)
            make_bitmap_clickable(bitmap, lambda col=colour: self.select(col))

            selection_sizer.Add(bitmap, 0, ALL, 5)

        main_sizer.Add(sizer, 0, ALIGN_CENTER)
        main_sizer.AddSpacer(20)

        main_sizer.Add(selection_sizer, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)

    def select(self, colour: Colour) -> None:
        """Selects a colour."""

        self.selected = colour
        self.EndModal(ID_OK)