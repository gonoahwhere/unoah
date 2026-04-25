from wx import (
    BitmapBundle,
    Colour,
    DEFAULT_FRAME_STYLE,
    EVT_MOVE,
    Font,
    FontInfo,
    Frame,
    GetClientDisplayRect,
    Image,
    IMAGE_QUALITY_HIGH,
    MAXIMIZE_BOX,
    Point,
    RESIZE_BORDER,
    Size,
    WANTS_CHARS,
)
from typing import TYPE_CHECKING
from functools import cache
from pathlib import Path
from sys import platform
from json import loads
from enum import Enum

if TYPE_CHECKING:
    from wx import SizeEvent

ASSETS_DIR = Path(__file__).parent.parent / 'assets'
"""The game's assets path."""

IMAGES_DIR = ASSETS_DIR / 'images'
"""The game's image assets path."""

FONTS_DIR = ASSETS_DIR / 'fonts'
"""The game's font assets path."""

AUDIO_DIR = ASSETS_DIR / 'audio'
"""The game's audio assets path."""

class Theme(Enum):
    """The game's supported themes."""

    __slots__: tuple[str, ...] = ()

    OCEAN = 'ocean'
    SKY = 'sky'

    @property
    def flipped(self) -> 'Theme':
        """The flipped version of this theme."""

        return Theme.SKY if self is Theme.OCEAN else Theme.OCEAN

    def get_mapping(self) -> dict[str, str]:
        """Retrieves the colour mapping associated with this theme."""

        return loads((ASSETS_DIR / 'themes.json').read_text())[self.value]

DARK_THEMES: tuple[Theme, ...] = (Theme.OCEAN,)
"""The game's themes which are considered dark."""

class Config:
    """The game's configuration."""

    __slots__: tuple[str, ...] = (
        '_colour_mapping',
        'title',
        'subtitle',
        'size',
        'style',
        'maximized',
        'theme',
        'max_card_column_count',
        'max_card_row_count',
        'turn_timeout',
    )

    _colour_mapping: dict[str, str]
    """The game's colour mapping."""

    title: str
    """The game's title."""

    subtitle: str
    """The game's subtitle."""

    size: Size
    """The game's window size."""

    style: int
    """The game's window style."""

    maximized: bool
    """Whether the game's window is maximized upon startup."""

    theme: Theme
    """The game's current theme."""

    max_card_column_count: int
    """The game's maximum amount of card columns."""

    max_card_row_count: int
    """The game's maximum amount of card rows."""

    turn_timeout: int
    """The game's timeout for turns in milliseconds."""

    def __init__(
        self,
        title: str = 'UNOAH',
        subtitle: str = 'Every card you draw was chosen specifically to ruin your life.',
        size: Size | None = None,
        resizable: bool = False,
        maximized: bool = True,
        theme: Theme = Theme.OCEAN,
        max_card_column_count: int = 11,
        max_card_row_count: int = 3,
        turn_timeout: int = 800,
    ):
        self.update_theme(theme)

        self.title = title
        self.subtitle = subtitle
        self.size = size or Size(1200, 800)
        self.style = DEFAULT_FRAME_STYLE | WANTS_CHARS

        if not resizable:
            self.style &= ~RESIZE_BORDER

        # REMOVE 'ZOOM' FROM MACOS BEFORE WINDOW CREATION
        if platform == 'darwin':
            self.style &= ~MAXIMIZE_BOX

        self.maximized = maximized
        self.max_card_column_count = max_card_column_count
        self.max_card_row_count = max_card_row_count
        self.turn_timeout = turn_timeout

    def new_window(self) -> Frame:
        """Creates a game window based on the configuration."""

        frame = Frame(None, title=self.title, size=self.size, style=self.style)

        if platform == 'darwin':
            rect = GetClientDisplayRect()
            size = Size(rect.width, rect.height)
            position = Point(rect.x, rect.y)

            frame.SetPosition(position)
            frame.SetSize(size)
            frame.SetMinSize(size)
            frame.SetMaxSize(size)

            def on_move(event: SizeEvent) -> None:
                if frame.GetPosition() != position:
                    frame.SetPosition(position)

                event.Skip()

            frame.Bind(EVT_MOVE, on_move)

        return frame

    @property
    def is_dark_mode(self) -> bool:
        """Whether the configuration's theme is considered as dark mode."""

        return self.theme in DARK_THEMES

    @property
    def _cards_path(self) -> Path:
        """The current configuration's base card path."""

        return IMAGES_DIR / f'cards_{"dark" if self.is_dark_mode else "light"}'

    def update_theme(self, theme: Theme) -> None:
        """Updates the configuration based on the specific theme."""

        self.theme = theme
        self._colour_mapping = theme.get_mapping()

    def flip_theme(self) -> None:
        """Flips and updates the configuration's theme."""

        self.update_theme(self.theme.flipped)

    @property
    def toggle_image(self) -> BitmapBundle:
        """The current configuration's toggle image."""

        return BitmapBundle(Config.get_image(f'{"sun" if self.is_dark_mode else "moon"}.png'))

    @property
    def previous_image(self) -> BitmapBundle:
        """The current configuration's previous image."""

        return BitmapBundle(Config.get_image(f'previous_{"dark" if self.is_dark_mode else "light"}.png'))

    @property
    def next_image(self) -> BitmapBundle:
        """The current configuration's next image."""

        return BitmapBundle(Config.get_image(f'next_{"dark" if self.is_dark_mode else "light"}.png'))

    @property
    def max_per_page_card_count(self) -> int:
        """The current configuration's maximum amount of cards in a given page."""

        return self.max_card_column_count * self.max_card_row_count

    def get_colour(self, key: str) -> Colour:
        """Retrieves a colour from a mapping key."""

        return Colour(self._colour_mapping[key])

    @cache
    @staticmethod
    def get_image(*paths: str, scale: tuple[int, int] | None = None) -> Image:
        """Retrieves an image from a path."""

        image = Image(str(IMAGES_DIR.joinpath(*paths)))

        return (image if scale is None else image.Scale(scale[0], scale[1], IMAGE_QUALITY_HIGH))

    @cache
    @staticmethod
    def load_font(*paths: str) -> None:
        """Loads a font."""

        Font.AddPrivateFont(str(FONTS_DIR.joinpath(*paths)))

    @cache
    @staticmethod
    def new_font(size: int) -> Font:
        """Loads and/or creates a new Yukari font instance with the specified size."""

        # LOADS AND/OR CREATES FONT INSTANCE FROM THE SPECIFIED SIZE
        if platform.startswith('win'):
            # TRY DYNAMIC LOAD (WINDOWS)
            Config.load_font('yukari.ttf')

        font = Font(FontInfo(size).FaceName('Yukarimobile'))

        # FALLBACK IF FONT NOT FOUND
        if font.GetFaceName() != 'Yukarimobile':
            font = Font(FontInfo(size))

        return font

    @staticmethod
    def get_audio(*paths: str) -> Path:
        """Retrieves a joined audio path."""

        return AUDIO_DIR.joinpath(*paths)