from wx import (
    Bitmap,
    BitmapBundle,
    Brush,
    GraphicsContext,
    Image,
    IMAGE_QUALITY_HIGH,
    MemoryDC,
    StaticBitmap,
)
from typing import TYPE_CHECKING
from random import shuffle
from pathlib import Path
from enum import Enum
import random

from .config import Config

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Literal
    from ..panels.session import Session

    Colour = Literal['Blue', 'Orange', 'Pink', 'Green']

class SpecialCard(Enum):
    """A special card."""

    __slots__: tuple[str, ...] = ()

    SKIP = 'SKIP'
    REVERSE = 'REVERSE'
    DRAW2 = 'DRAW2'

class WildCard(Enum):
    """A wild card."""

    __slots__: tuple[str, ...] = ()

    WILD = 'WILD'
    DRAW4 = 'DRAW4'

class CardType(Enum):
    """A card's type."""

    __slots__: tuple[str, ...] = ()

    NUMBER = 'number'
    SPECIAL = 'special'
    WILD = 'wild'
    OTHER = 'other'

SPECIAL_CARDS: tuple[SpecialCard, ...] = tuple(iter(SpecialCard))
WILD_CARDS: tuple[WildCard, ...] = tuple(iter(WildCard))

COLOUR_MAPPING: dict[str, Colour] = {
    'B': 'Blue',
    'O': 'Orange',
    'P': 'Pink',
    'G': 'Green',
}

IMAGE_CACHE: dict[str, dict[str, Bitmap | Image]] = {}

class Card:
    """A card's information."""

    __slots__: tuple[str, ...] = ('config', 'key')

    config: Config
    """The game's configuration."""

    key: str
    """The card's key."""

    def __init__(self, config: Config, key: str):
        self.config = config
        self.key = key

    @property
    def path(self) -> Path:
        """The card's image path."""

        return self.config._cards_path / f'{self.key}.png'

    @property
    def type(self) -> CardType:
        """The card's type."""

        if self.key[0].isdigit():
            return CardType.NUMBER
        elif self.key.split('_')[0] in WildCard:
            return CardType.WILD
        elif any(self.key.startswith(special.value) for special in SPECIAL_CARDS):
            return CardType.SPECIAL
        return CardType.OTHER

    @property
    def colour(self) -> Colour | None:
        """The card's colour."""

        card_type = self.type

        return (
            COLOUR_MAPPING[self.key[-1]]
            if card_type is CardType.NUMBER
            or card_type is CardType.SPECIAL
            or (card_type is CardType.WILD and '_' in self.key)
            else None
        )

    @property
    def is_draw(self) -> bool:
        """Whether the card is a draw card."""

        return 'DRAW' in self.key

    @property
    def is_repeat(self) -> bool:
        """Whether the card is a repeat card."""

        return self.key.startswith('SKIP') or self.key.startswith('REVERSE')

    @property
    def is_7_0(self) -> bool:
        """Whether the card is a 7 or 0."""

        return self.key[0] in ('0', '7')

    def _cache_image(self, key: str, fallback: Callable[[], Bitmap | Image]) -> Bitmap | Image:
        """Retrieves an image from the internal cache, creates and stores one if it's not cached."""

        if cached_images := IMAGE_CACHE.get(self.key):
            if cached_image := cached_images.get(key):
                return cached_image
        else:
            IMAGE_CACHE[self.key] = {}

        cached_image = IMAGE_CACHE[self.key][key] = fallback()

        return cached_image

    def set_wild_card_colour(self, colour: Colour) -> None:
        """Modifies the card's wild card colour."""

        self.key += f'_{colour[0]}'

    def get_image(self, size: tuple[int, int]) -> Bitmap | Image:
        """Retrieves a cached image of this card."""

        key = f'i:{self.config.theme}:{".".join(map(str, size))}'

        return self._cache_image(key, lambda: Image(str(self.path)).Scale(size[0], size[1], IMAGE_QUALITY_HIGH),)

    def _new_stack_image(
        self,
        quantity: int = 4,
        size: tuple[int, int] = (116, 168),
        offset: tuple[int, int] = (2, 5),
    ) -> Bitmap:
        """Creates a new stack image."""

        offset_x, offset_y = offset

        base = Bitmap(size[0] + (offset_x * quantity), size[1] + (offset_y * quantity))
        image = Bitmap(self.get_image(size))

        dc = MemoryDC(base)
        dc.SetBackground(Brush(self.config.get_colour('bg_primary')))
        dc.Clear()

        gc = GraphicsContext.Create(dc)

        # PASTE THE CARDS WITH OFFSET
        for i in range(quantity):
            gc.DrawBitmap(image, i * offset_x, i * offset_y, size[0], size[1])

        del dc

        return base

    def new_stack_image(
        self,
        quantity: int = 4,
        size: tuple[int, int] = (116, 168),
        offset: tuple[int, int] = (2, 5),
    ) -> Bitmap | Image:
        """Creates a new cached stack image."""

        if quantity == 1:
            return self.get_image(size)

        pair_key = lambda pair: '.'.join(map(str, pair))
        key = f's:{self.config.theme}:{quantity}:{pair_key(size)}:{pair_key(offset)}'

        return self._cache_image(key, lambda: self._new_stack_image(quantity, size, offset))

    @staticmethod
    def get_all(config: Config) -> Generator['Card']:
        """Retrieves all possible cards excluding those with the other type."""

        for colour in COLOUR_MAPPING.keys():
            # NUMBER CARDS
            for number in range(0, 10):
                yield Card(config, f'{number}{colour}')

            # SPECIAL CARDS
            for special in SPECIAL_CARDS:
                yield Card(config, f'{special.value}_{colour}')

        # WILD CARDS
        for wild in WILD_CARDS:
            yield Card(config, wild.value)

    @staticmethod
    def get_deck() -> list[str]:
        """Retrieves a full deck of card keys."""

        deck = []

        # NUMBER CARDS
        for colour in COLOUR_MAPPING.keys():
            # 1x 0
            deck.append(f'0{colour}')

            # 2x 1-9
            for number in range(1, 10):
                deck.extend([f'{number}{colour}'] * 2)

            # SPECIAL CARDS
            # 2x FOR EACH COLOUR
            for special in SPECIAL_CARDS:
                deck.extend([f'{special.value}_{colour}'] * 2)

        # WILD CARDS
        deck.extend([wild.value for wild in WILD_CARDS] * 4)

        return deck

    @staticmethod
    def new_hands(player_cards: int) -> tuple[list[str], list[str]]:
        """Creates player and opponent hands from a shuffled deck of cards."""

        deck = Card.get_deck()
        shuffle(deck)

        return deck[:player_cards], deck[player_cards : player_cards * 2]

    @staticmethod
    def new_playable(config: Config) -> 'Card':
        """Retrieves a new random playable card."""

        return random.choice(list(filter(lambda card: card.type is not CardType.OTHER, Card.get_all(config))))

    @staticmethod
    def new_middle(config: Config) -> 'Card':
        """Retrieves a new random middle card."""

        return random.choice(list(filter(lambda card: card.type is CardType.NUMBER, Card.get_all(config))))

class OpponentCardColumn:
    """An opponent card column."""

    __slots__: tuple[str, ...] = ('session', 'image', 'quantity')

    session: Session
    """The column's parent session."""

    image: StaticBitmap
    """The column's image."""

    quantity: int
    """The column's amount of opponent cards."""

    def __init__(self, session: Session):
        self.session = session
        self.image = StaticBitmap(session.panel, bitmap=BitmapBundle(session.background_card.get_image((80, 120))),)
        self.quantity = 1

    def _update_image(self) -> None:
        """Updates the column's image based on its quantity."""

        self.image.SetBitmap(
            BitmapBundle(self.session.background_card.new_stack_image(self.quantity, (80, 120), (0, 35))))

    def update(self, quantity: int) -> None:
        """Updates the column's quantity."""

        if (self.quantity == quantity or self.quantity > self.session.game.config.max_card_row_count):
            return

        self.quantity = quantity
        self._update_image()

    def reflect_theme(self) -> None:
        """Reflects the column based on the game's theme."""

        self._update_image()