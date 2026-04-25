from wx import Cursor, CURSOR_HAND, EVT_LEFT_DCLICK, EVT_LEFT_DOWN, StaticBitmap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wx import BoxSizer, FlexGridSizer, Window
    from collections.abc import Callable
    from typing import Any
    from ..game import Game

def make_bitmap_clickable(bitmap: StaticBitmap, callback: Callable[[], None]) -> None:
    """Adds click handling to a StaticBitmap."""

    wrapped_callback = lambda _: callback()

    bitmap.SetCursor(Cursor(CURSOR_HAND))
    bitmap.Bind(EVT_LEFT_DCLICK, wrapped_callback)
    bitmap.Bind(EVT_LEFT_DOWN, wrapped_callback)

def safe_add_to_sizer(sizer: BoxSizer | FlexGridSizer, window: Window, *args: Any, **kwargs: Any):
    """Safely adds a window to a sizer by detaching its containing sizer first if it has one."""

    if existing_sizer := window.GetContainingSizer():
        existing_sizer.Detach(window)

    sizer.Add(window, *args, **kwargs)

class RepaintGuard:
    """A guard for repainting window UI without flickering."""

    __slots__: tuple[str, ...] = ('game', 'update_layout')

    game: Game
    """The parent game instance."""

    update_layout: bool
    """Indicates whether Layout() is called before repainting resumes."""

    def __init__(self, game: Game, *, update_layout: bool = True):
        self.game = game
        self.update_layout = update_layout

    def __enter__(self) -> 'RepaintGuard':
        self.game.repaint_refcount += 1

        if self.game.repaint_refcount == 1:
            self.game.window.Freeze()

        return self

    def __exit__(self, *_, **__) -> None:
        self.game.repaint_refcount -= 1

        if self.game.repaint_refcount == 0:
            if self.update_layout:
                self.game.window.Layout()

            self.game.window.Thaw()