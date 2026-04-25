from wx import (
    App,
    BoxSizer,
    EVT_CHAR_HOOK,
    EVT_CLOSE,
    EXPAND,
    VERTICAL,
    WXK_ESCAPE,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wx import CloseEvent, KeyEvent, Frame
    from .panels.panel import Panel

from .utils.audio import PriorityPlayer
from .utils.config import Config
from .panels.main_menu import MainMenu
from .panels.information import Information
from .panels.session import Session
from .panels.statistics import Statistics
from .utils.util import RepaintGuard

class Game(App):
    """An UNOAH game application."""

    __slots__: tuple[str, ...] = (
        'config',
        'window',
        'repaint_refcount',
        'player',
        'main_menu',
        'session',
        'information',
        'statistics',
        'current_panel',
        'closed',
    )

    config: Config
    """The game's configuration."""

    window: Frame
    """The game's main window."""

    repaint_refcount: int
    """The game's repaint reference count."""

    player: PriorityPlayer
    """The game's audio player."""

    main_menu: MainMenu
    """The game's main menu."""

    session: Session
    """The game's playing session."""

    information: Information
    """The game's information panel."""

    statistics: Statistics
    """The game's statistics panel."""

    current_panel: Panel
    """The game's current panel."""

    closed: bool
    """Whether the game has been closed."""

    def __init__(self, config: Config):
        super().__init__()

        self.config = config
        self.window = config.new_window()
        self.window.CenterOnScreen()

        self.repaint_refcount = 0

        self.player = PriorityPlayer()
        self.player.add('cards', 0)
        self.player.add('challenge', 1)
        self.player.add('noah1', 1)
        self.player.add('noah2', 1)
        self.player.add('noah3', 1)
        self.player.add('loss', 2)
        self.player.add('win', 2)

        with self.repaint():
            self.main_menu = MainMenu(self)
            self.session = Session(self)
            self.information = Information(self)
            self.statistics = Statistics(self)

            # ATTACH TO FRAME
            frame_sizer = BoxSizer(VERTICAL)
            frame_sizer.Add(self.main_menu.panel, 1, EXPAND)
            frame_sizer.Add(self.session.panel, 2, EXPAND)
            frame_sizer.Add(self.information.panel, 3, EXPAND)
            frame_sizer.Add(self.statistics.panel, 4, EXPAND)

            self.window.SetFocus()
            self.window.Bind(EVT_CHAR_HOOK, self.on_key)
            self.window.Bind(EVT_CLOSE, self.close)
            self.window.SetSizer(frame_sizer)

            self.closed = False

    def reflect_theme(self) -> None:
        """Reflect the game based on the game's theme."""

        with self.repaint(update_layout=False):
            self.main_menu.reflect_theme()
            self.session.reflect_theme()
            self.information.reflect_theme()
            self.statistics.reflect_theme()

    def flip_theme(self) -> None:
        """Flips and updates the game's theme."""

        self.config.flip_theme()
        self.reflect_theme()

    def on_key(self, event: KeyEvent) -> None:
        """Handles key pressing events."""

        if event.GetKeyCode() == WXK_ESCAPE and not self.session.is_opponent_turn:
            self.open('main_menu')

        event.Skip()

    def open(self, panel_name: str) -> None:
        """Opens a panel."""

        with self.repaint():
            self.current_panel.panel.Hide()
            self.current_panel.cleanup()

            getattr(self, panel_name).restore()

    def start(self) -> None:
        """Starts the game's window loop."""

        self.window.Show()
        self.MainLoop()

    def repaint(self, *, update_layout: bool = True) -> RepaintGuard:
        """Creates a new guard for repainting the game's UI without flickering."""

        return RepaintGuard(self, update_layout=update_layout)

    def close(self, event: CloseEvent) -> None:
        """Handles a close event."""

        self.closed = True

        event.Skip()