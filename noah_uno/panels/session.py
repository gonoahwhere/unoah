from wx import (
    ALIGN_CENTER,
    ALL,
    Bitmap,
    BitmapBundle,
    BOTTOM,
    BoxSizer,
    Brush,
    CallAfter,
    CallLater,
    Cursor,
    CURSOR_HAND,
    CURSOR_NO_ENTRY,
    EVT_LEFT_DCLICK,
    EVT_LEFT_DOWN,
    GraphicsContext,
    HORIZONTAL,
    Image,
    MemoryDC,
    Point,
    StaticBitmap,
    TOP,
    VERTICAL,
)
from typing import TYPE_CHECKING
from math import ceil
import random

from ..utils.card import Card, CardType, COLOUR_MAPPING, OpponentCardColumn
from ..dialogs.draw4_challenge import Draw4Challenge
from ..dialogs.game_over import GameOver
from .panel import Panel
from ..utils.scores import record_win
from ..utils.util import make_bitmap_clickable, safe_add_to_sizer
from ..dialogs.wild_card_selection import WildCardSelection
from ..utils.config import Config

if TYPE_CHECKING:
    from ..utils.card import Colour
    from ..game import Game

class Session(Panel):
    """A game session."""

    __slots__: tuple[str, ...] = (
        'middle_card',
        'middle_card_image',
        'background_card_image',
        'opponent_cards',
        'opponent_card_sizer',
        'opponent_card_columns',
        'is_opponent_turn',
        'repeat_opponent_turn',
        'player_cards',
        'player_card_columns',
        'player_card_sizer',
        'player_card_page',
        'player_card_previous_image',
        'player_card_next_image',
        'stacked_card_count',
        'pickup_card',
        'pickup_card_stack_image',
        'game_over',
        'has_called_noah',
        'opponent_has_called_noah',
        'noah_button'
    )

    middle_card: Card | None
    """The game session's middle card."""

    middle_card_image: StaticBitmap
    """The game session's middle card image."""

    background_card_image: BitmapBundle
    """The game session's background card image."""

    opponent_cards: list[Card]
    """The game session's list of individual opponent cards."""

    opponent_card_sizer: BoxSizer
    """The game session's opponent card sizer."""

    opponent_card_columns: list[OpponentCardColumn]
    """The game session's list of opponent card columns."""

    is_opponent_turn: bool
    """Whether it's currently the opponent's turn."""

    repeat_opponent_turn: bool
    """Whether to repeat current player's turn."""

    player_cards: list[Card]
    """The game session's list of individual player cards."""

    player_card_columns: list[Bitmap]
    """The game session's list of player card images grouped in columns."""

    player_card_sizer: BoxSizer
    """The game session's player card sizer."""

    player_card_page: int
    """The game session's player card page as a zero based index."""

    player_card_previous_image: StaticBitmap
    """The game session's image for reverting to the previous player card page."""

    player_card_next_image: StaticBitmap
    """The game session's image for advancing to the next player card page."""

    stacked_card_count: int
    """The game session's current stacked card count."""

    pickup_card: Card
    """The game session's pickup card."""

    pickup_card_stack_image: StaticBitmap
    """The game session's pickup card stack image."""

    game_over: bool
    """Whether it is game over."""

    has_called_noah: bool
    """Whether the player has called NOAH while only having one card."""

    opponent_has_called_noah: bool
    """Whether the opponent called NOAH when they only have one card."""
    
    def __init__(self, game: Game):
        super().__init__(game)

        self.middle_card = None

        # BACK OF THE CARDS
        self.background_card_image = BitmapBundle(self.background_card.get_image((80, 120)))

        self.opponent_card_columns = []
        self.player_cards = []
        self.is_opponent_turn = False

        self.player_card_previous_image = StaticBitmap(self.panel, bitmap=game.config.previous_image)
        make_bitmap_clickable(self.player_card_previous_image, self.previous_player_card_page)

        self.player_card_next_image = StaticBitmap(self.panel, bitmap=game.config.next_image)
        make_bitmap_clickable(self.player_card_next_image, self.next_player_card_page)

        # PICKUP PILE (STACK FACED DOWN)
        self.pickup_card = Card(game.config, 'PICKUP')
        self.pickup_card_stack_image = StaticBitmap(self.panel, bitmap=BitmapBundle(self.pickup_card.new_stack_image()),)
        make_bitmap_clickable(self.pickup_card_stack_image, self.draw)

        # NOAH BUTTON - WHEN PLAYER/OPPONENT HAS ONE CARD REMAINING
        self.has_called_noah = False
        self.opponent_has_called_noah = False
        self.noah_button = self.new_button('NOAH', lambda: self.call_noah())
        self.noah_button.SetMinSize((225, 65))
        self.noah_button.SetSize(self.noah_button.GetBestSize())
        self.noah_button.SetCursor(Cursor(CURSOR_HAND))
        self.noah_button.Hide()

        self.game_over = True

    def call_noah(self) -> None:
        """Called when the player presses the NOAH button."""

        if len(self.player_cards) != 1 or self.is_opponent_turn:
            return

        self.has_called_noah = True
        self.noah_button.Hide()

        self.game.player.play(f'noah{random.randint(1, 3)}')

    def _apply_noah_penalty_player(self) -> None:
        """Draws two cards as a penalty for the player not calling NOAH."""

        for _ in range(2):
            if self.is_player_card_count_overflown:
                if self.is_in_last_player_card_page:
                    self.player_card_page += 1
                else:
                    self.player_card_page = self.add_opponent_card_count - 1

            self._draw()

    def _apply_noah_penalty_opponent(self) -> None:
        """Draws two cards as a penalty for the opponent not calling NOAH."""

        for _ in range(2):
            self._opponent_draw()

    @property
    def background_card(self) -> Card:
        """The game session's background card."""

        return Card(self.game.config, 'BACKGROUND')

    def get_player_card(self, index: int) -> Card:
        """Retrieves a player card from the current page."""

        real_index = (self.player_card_page * self.game.config.max_per_page_card_count) + index

        if real_index < 0 or real_index >= len(self.player_cards):
            raise IndexError(f'Card index out of range: {real_index} (len={len(self.player_cards)}, page={self.player_card_page}, index={index})')

        return self.player_cards[real_index]

    @property
    def in_page_player_card_count(self) -> int:
        """The game session's amount of player cards in the current page."""

        max_count_per_page = self.game.config.max_per_page_card_count

        return min(len(self.player_cards) - (self.player_card_page * max_count_per_page), max_count_per_page,)

    @property
    def is_in_last_player_card_page(self) -> bool:
        """Whether the game session is in the last page of the player cards."""

        return (self.player_card_page + 1) >= self.player_card_page_count

    @property
    def is_player_card_count_overflown(self) -> bool:
        """Whether the game session's current page has overflown with number of player cards."""

        max_count_per_page = self.game.config.max_per_page_card_count

        return (len(self.player_cards) - (self.player_card_page * max_count_per_page)) >= max_count_per_page
    
    @property
    def player_card_page_count(self) -> int:
        """The game session's amount of player card pages."""

        return ceil(len(self.player_cards) / self.game.config.max_per_page_card_count)

    @property
    def player_card_column_count(self) -> int:
        """The game session's number of columns for player cards in the current page."""

        return min(self.in_page_player_card_count, self.game.config.max_card_column_count)

    def previous_player_card_page(self) -> None:
        """Tries to revert back to the previous player card page."""

        if self.player_card_page == 0:
            return

        self.player_card_page -= 1

        with self.game.repaint():
            self.update_player_cards()

    def next_player_card_page(self) -> None:
        """Tries to advance to the next player card page."""

        if self.is_in_last_player_card_page:
            return

        self.player_card_page += 1

        with self.game.repaint():
            self.update_player_cards()

    def can_play(self, card: Card, *, player: bool) -> bool:
        """Whether a card can be played on top of the current middle card."""

        if TYPE_CHECKING:
            assert self.middle_card is not None

        if (
            self.middle_card.key.startswith('DRAW4') and card.key.startswith('DRAW2')
        ) or (
            self.middle_card.key.startswith('DRAW2')
            and card.key.startswith('DRAW4')
            and any(card.key.startswith('DRAW2') for card in getattr(self, f'{"player" if player else "opponent"}_cards'))
        ):
            return False
        elif card.type is CardType.WILD or card.colour == self.middle_card.colour:
            return True

        # CHECK IF CARD MATCHES MIDDLE CARD'S VALUE
        card_value = card.key[:-1] if card.colour else card.key
        middle_card_value = (
            self.middle_card.key[:-1]
            if self.middle_card.colour
            else self.middle_card.key
        )

        return card_value == middle_card_value
    
    def stack(self, quantity: int, *, player: bool) -> bool:
        """Stacks a +2 or +4 card."""

        self.stacked_card_count += quantity

        if player:
            result = not self.opponent_can_stack_back

            if result:
                self.opponent_draw()
        else:
            result = not self.can_stack_back

            if result:
                self.draw(stacked=True)

        return result

    @property
    def can_stack_back(self) -> bool:
        """Whether the player can respond to the card stack."""

        return any(
            self.can_play(card, player=True)
            for card in self.player_cards
            if card.is_draw
        )

    @property
    def opponent_can_stack_back(self) -> bool:
        """Whether the opponent can respond to the card stack."""

        return any(
            self.can_play(card, player=False)
            for card in self.opponent_cards
            if card.is_draw
        )

    def has_stack_penalty(self, card: Card) -> bool:
        """Whether the chosen card results carries a card stack penalty."""

        return bool(self.stacked_card_count) and not card.is_draw

    def resolve_challenge(self, colour: Colour | None, had_playable: bool) -> bool:
        if self.opponent_accepts_challenge:
            self.game.player.play('challenge')

            if had_playable:
                self.draw(4)
            else:
                self.opponent_draw(6)

            return True
        
        return False
    
    def resolve_opponent_challenge(self, colour: Colour | None) -> bool:
        """Resolves an opponent's draw 4 challenge."""

        selection = Draw4Challenge(self)
        selection.ShowModal()

        if selection.challenged:
            self.game.player.play('challenge')

            if any(card for card in self.opponent_cards if card.colour == colour):
                self.opponent_draw(4)
            else:
                self.draw(6)

            return True

        return False
    
    def position_noah_button(self) -> None:
        panel_w, panel_h = self.panel.GetClientSize()

        self.noah_button.Layout()
        btn_w, btn_h = self.noah_button.GetBestSize()

        margin = 15

        x = panel_w - btn_w - margin - 50
        y = panel_h - btn_h - margin - 50

        self.noah_button.SetPosition((x, y))

    def update_player_cards(self) -> None:
        """Updates the player cards."""

        if not self.player_cards:
            for child in self.player_card_sizer.GetChildren():
                child.GetWindow().Hide()

            self.noah_button.Hide()

            return

        self.game.player.play('cards')

        at_one_card = len(self.player_cards) == 1

        if not at_one_card:
            self.has_called_noah = False

        should_show = at_one_card and not self.has_called_noah

        if should_show:
            self.position_noah_button()
            self.noah_button.Show()
        else:
            self.noah_button.Hide()

        sufficient_page_count_for_switches = self.player_card_page_count > 1

        self.player_card_previous_image.Show(sufficient_page_count_for_switches and self.player_card_page > 0)
        self.player_card_next_image.Show(sufficient_page_count_for_switches and not self.is_in_last_player_card_page)

        column_count = self.player_card_column_count
        sizer_children = self.player_card_sizer.GetChildren()

        for i in range(0, column_count):
            self.update_player_card_column(i)

        for i in range(len(sizer_children) - 1, self.player_card_column_count - 1, -1):
            sizer_children[i].GetWindow().Hide()

    def update_player_card_column(self, index: int) -> None:
        """Updates a player card column."""

        background_colour = Brush(self.game.config.get_colour('bg_primary'))
        count = self.in_page_player_card_count

        sizer_children = self.player_card_sizer.GetChildren()
        sizer_children_count = len(sizer_children)

        column_image = self.player_card_columns[index]

        column_count = self.get_column_player_card_count(index)
        new_height = 120 + ((column_count - 1) * 35)

        if new_height != column_image.GetHeight():
            column_image = self.player_card_columns[index] = Bitmap(80, new_height)

        dc = MemoryDC(column_image)
        dc.SetBackground(background_colour)
        dc.Clear()

        gc = GraphicsContext.Create(dc)

        y = 0

        # PASTE THE CARDS WITH OFFSET
        for j in range(index, count, self.game.config.max_card_column_count):
            image = self.get_player_card(j).get_image((80, 120))

            if TYPE_CHECKING:
                assert isinstance(image, Image)

            gc.DrawBitmap(Bitmap(image), 0, y, 80, 120)

            y += 35

        del dc

        column_image = BitmapBundle(column_image)

        if index < sizer_children_count:
            existing_column_image = sizer_children[index].GetWindow()

            existing_column_image.SetBitmap(column_image)
            existing_column_image.Show()
        else:
            static_column_image = StaticBitmap(self.panel, bitmap=column_image)

            play = lambda event: self.play(event.Position, index)

            static_column_image.SetCursor(Cursor(CURSOR_HAND))
            static_column_image.Bind(EVT_LEFT_DCLICK, play)
            static_column_image.Bind(EVT_LEFT_DOWN, play)

            self.player_card_sizer.Add(static_column_image, 1, ALL, 5)

    def get_column_player_card_count(self, index: int) -> int:
        """Retrieves the number of player cards in the given column in the current page."""

        return ceil((self.in_page_player_card_count - index) / self.player_card_column_count)

    def update_opponent_cards(self) -> None:
        """Updates the opponent cards."""

        if not self.opponent_cards:
            for child in self.opponent_card_sizer.GetChildren():
                child.GetWindow().Hide()

            return

        self.game.player.play('cards')

        card_count = len(self.opponent_cards)
        card_column_count = len(self.opponent_card_columns)
        max_card_column_count = self.game.config.max_card_column_count

        new_card_column_count = min(card_count, max_card_column_count)

        if new_card_column_count > card_column_count:
            for _ in range(new_card_column_count - card_column_count):
                self.add_opponent_card_column()
        elif new_card_column_count < card_column_count:
            for _ in range(card_column_count - new_card_column_count):
                column = self.opponent_card_columns.pop()

                self.opponent_card_sizer.Detach(column.image)
                column.image.Destroy()

        max_row_count = card_count // new_card_column_count
        new_max_row_count = min(max_row_count + 1, self.game.config.max_card_row_count)
        full_column_count = card_count % new_card_column_count

        for i in range(0, full_column_count):
            self.opponent_card_columns[i].update(new_max_row_count)

        for i in range(full_column_count, new_card_column_count):
            self.opponent_card_columns[i].update(max_row_count)

    def add_opponent_card_column(self) -> None:
        """Adds a new opponent card column."""

        column = OpponentCardColumn(self)

        self.opponent_card_sizer.Add(column.image, 0, ALL, 5)
        self.opponent_card_columns.append(column)

    def swap(self, card: Card, *, has_stack_penalty: bool = False) -> None:
        """Swaps the player and opponent cards."""

        self.player_cards, self.opponent_cards = self.opponent_cards, self.player_cards
        self.player_card_page = min(self.player_card_page, self.player_card_page_count - 1)

        with self.game.repaint():
            self.middle_card_image.SetBitmap(BitmapBundle(card.get_image((116, 168))))

            if has_stack_penalty:
                self.draw(stacked=True)

            self.update_player_cards()
            self.update_opponent_cards()

    def _draw(self, card: Card | None = None) -> None:
        """Draws a card."""

        self.player_cards.append(card or Card.new_playable(self.game.config))

    def draw(self, _quantity: int | None = None, *, stacked: bool = False) -> None:
        """Makes the player draw the specified amount of cards."""

        if not stacked and not _quantity and self.stacked_card_count:
            self.draw(stacked=True)
            self.opponent_turn()
            return

        had_playable_before_draw = any(self.can_play(card, player=True) for card in self.player_cards)

        quantity = _quantity or 1

        if stacked:
            quantity = self.stacked_card_count

            self.stacked_card_count = 0

        for _ in range(0, quantity):
            if self.is_player_card_count_overflown:
                if self.is_in_last_player_card_page:
                    self.player_card_page += 1
                else:
                    self.player_card_page = self.player_card_page_count - 1

            self._draw()

        ordinary_draw = not stacked and not _quantity
        update_middle_card_image = False
        manual_repaint = True
        opponent_turn = False
        drawn_card = None

        if ordinary_draw:
            drawn_card = self.player_cards[-1]
            opponent_turn = True

            if self.can_play(drawn_card, player=True):
                if drawn_card.type is CardType.WILD:
                    selection = WildCardSelection(self, drawn_card, force=True)
                    selection.ShowModal()

                    if TYPE_CHECKING:
                        assert selection.selected is not None

                    drawn_card.set_wild_card_colour(selection.selected)

                self.middle_card = drawn_card
                self.player_cards.remove(drawn_card)

                if not self.in_page_player_card_count and self.player_card_page > 0:
                    self.player_card_page -= 1

                update_middle_card_image = True

                if drawn_card.is_7_0:
                    self.swap(drawn_card)

                    manual_repaint = False
                else:
                    if drawn_card.key.startswith('DRAW2'):
                        if self.stack(2, player=True):
                            opponent_turn = False
                    elif drawn_card.key.startswith('DRAW4'):
                        if (not self.resolve_challenge(drawn_card.colour, had_playable_before_draw)) and self.stack(4, player=True):
                            opponent_turn = False
                    elif drawn_card.is_repeat:
                        opponent_turn = False

        if manual_repaint:
            with self.game.repaint():
                if update_middle_card_image:
                    if TYPE_CHECKING:
                        assert drawn_card is not None

                    self.middle_card_image.SetBitmap(BitmapBundle(drawn_card.get_image((116, 168))))

                self.update_player_cards()

        if opponent_turn and ordinary_draw:
            self.opponent_turn()

    def play(self, cursor_position: Point, column_index: int) -> None:
        """Plays a card."""

        if self.is_opponent_turn:
            return
 
        column_player_cards_count = self.get_column_player_card_count(column_index)
        column_player_card_index = min(cursor_position.y // 35, column_player_cards_count - 1)

        card = self.get_player_card((column_player_card_index * self.player_card_column_count) + column_index)

        had_playable_before_draw = any(self.can_play(c, player=True) for c in self.player_cards if c is not card)

        if not self.can_play(card, player=True):
            return

        has_stack_penalty = self.has_stack_penalty(card)

        if card.type is CardType.WILD and (len(self.player_cards) > 1 or has_stack_penalty):
            selection = WildCardSelection(self, card)
            selection.ShowModal()

            if selection.selected is None:
                return

            card.set_wild_card_colour(selection.selected)

        # CARD CAN BE PLAYED, MOVE CARD TO MIDDLE PILE
        self.middle_card = card

        # REMOVE CARD FROM PLAYER'S HAND
        self.player_cards.remove(card)

        if not self.in_page_player_card_count and self.player_card_page > 0:
            self.player_card_page -= 1

        if card.is_7_0:
            if self.player_cards:
                self.swap(card, has_stack_penalty=has_stack_penalty)
                next_turn = bool(self.opponent_cards)
            else:
                with self.game.repaint():
                    self.middle_card_image.SetBitmap(BitmapBundle(card.get_image((116, 168))))
                    self.update_player_cards()
                CallAfter(self.finish, True)
                return 

        else:
            next_turn = bool(self.player_cards)

            with self.game.repaint():
                # UPDATE MIDDLE CARD IMAGE
                self.middle_card_image.SetBitmap(BitmapBundle(card.get_image((116, 168))))

                if has_stack_penalty:
                    self.draw(stacked=True)

                self.update_player_cards()

                # CHECK WIN BEFORE ANYTHING ELSE, EVEN SPECIAL CARDS
                if next_turn:
                    if card.key.startswith('DRAW2'):
                        if self.stack(2, player=True):
                            return
                    elif card.key.startswith('DRAW4'):
                        if (not self.resolve_challenge(card.colour, had_playable_before_draw)) and self.stack(4, player=True):
                            return
                    elif card.is_repeat:
                        return

        if next_turn:
            self.opponent_turn()
        else:
            if not self.has_called_noah:
                self._apply_noah_penalty_player()

                with self.game.repaint():
                    self.update_player_cards()

                self.opponent_turn()
            else:
                CallAfter(self.finish, True)

    def player_turn(self) -> None:
        """Signals a player turn."""

        self.is_opponent_turn = False

        self.pickup_card_stack_image.SetCursor(Cursor(CURSOR_HAND))

        for child in self.player_card_sizer.GetChildren():
            child.GetWindow().SetCursor(Cursor(CURSOR_HAND))

    def get_most_effective_opponent_colour(self, *, including_middle_cards: bool = True) -> Colour | None:
        """Retrieves the most effective colour from the opponent's hands."""

        if TYPE_CHECKING:
            assert self.middle_card is not None

        needs_7_0 = len(self.player_cards) > len(self.opponent_cards)
        middle_card_colour = self.middle_card.colour
        colour_effectivity_map = {}

        for possible_card in self.opponent_cards:
            if possible_card_colour := possible_card.colour:
                if including_middle_cards or possible_card_colour != middle_card_colour:
                    score = colour_effectivity_map.get(possible_card_colour, 0) + 1

                    if needs_7_0 and possible_card.is_7_0:
                        score += 3
                    elif possible_card.is_draw:
                        score += 2
                    elif possible_card.is_repeat:
                        score += 1

                    colour_effectivity_map[possible_card_colour] = score

        sorted_colour_effectivity_map = sorted(colour_effectivity_map.items(), key=lambda entry: entry[1], reverse=True)

        try:
            return (
                sorted_colour_effectivity_map[0][0]
                if sorted_colour_effectivity_map
                else random.choice(list(COLOUR_MAPPING.values()))
            )
        except IndexError:
            pass

    def get_most_effective_opponent_card(self, playable_cards: list[Card]) -> Card:
        """Retrieves the most effective card from the opponent's hands."""

        chosen_colour = self.get_most_effective_opponent_colour()

        if TYPE_CHECKING:
            assert self.middle_card is not None

        if (
            self.middle_card.type is CardType.WILD
            and self.middle_card.colour != chosen_colour
        ):
            try:
                return next(card for card in playable_cards if card.type is CardType.WILD)
            except StopIteration:
                pass

        needs_7_0 = len(self.player_cards) > len(self.opponent_cards)

        try:
            return next(card for card in playable_cards
                if (
                    (needs_7_0 and card.is_7_0)
                    or card.is_draw
                    or card.is_repeat
                    or (chosen_colour is not None and card.colour == chosen_colour)
                )
            )
        except StopIteration:
            if all(card.colour is None for card in playable_cards):
                try:
                    return next(card for card in playable_cards if card.type is CardType.WILD)
                except StopIteration:
                    pass

        return random.choice(playable_cards)
    
    @property
    def opponent_accepts_challenge(self) -> bool:
        """Whether the opponent accepts a draw 4 challenge."""

        card_count = len(self.player_cards)
        threshold = 0.4 if card_count >= 4 else 0.75

        return random.random() < threshold

    def _opponent_draw(self) -> None:
        """The opponent draws a card because no valid play exists."""

        self.opponent_cards.append(Card.new_playable(self.game.config))

        if len(self.opponent_cards) > 1:
            self.opponent_has_called_noah = False

    def opponent_draw(self, quantity: int | None = None) -> None:
        """Makes the opponent draw the specified amount of cards."""

        if quantity is None:
            quantity = self.stacked_card_count

            self.stacked_card_count = 0

        for _ in range(0, quantity):
            self._opponent_draw()

        with self.game.repaint():
            self.update_opponent_cards()

    def _opponent_play(self, card: Card) -> tuple[bool, bool]:
        """The opponent plays a chosen card."""

        cards_before_play = len(self.opponent_cards)
        is_going_to_one_card = cards_before_play == 2 and not (card.is_7_0 and len(self.player_cards) != 1)

        if is_going_to_one_card:
            self.opponent_has_called_noah = random.random() > 0.5

            if self.opponent_has_called_noah:
                self.game.player.play(f'noah{random.randint(1, 3)}')
        else:
            self.opponent_has_called_noah = False

        self.middle_card = card
        self.opponent_cards.remove(card)

        has_stack_penalty = self.has_stack_penalty(card)

        if card.is_7_0:
            if self.opponent_cards:
                self.swap(card, has_stack_penalty=has_stack_penalty)

            if not self.opponent_cards and not self.opponent_has_called_noah:
                self._apply_noah_penalty_opponent()
                with self.game.repaint():
                    self.update_opponent_cards()

            return not self.player_cards, False
        else:
            with self.game.repaint():
                self.middle_card_image.SetBitmap(BitmapBundle(card.get_image((116, 168))))

                if has_stack_penalty:
                    self.opponent_draw()

                if card.key.startswith('DRAW2'):
                    if self.stack(2, player=False):
                        self.repeat_opponent_turn = True
                elif card.key.startswith('DRAW4'):
                    if (not self.resolve_opponent_challenge(card.colour)) and self.stack(4, player=False):
                        self.repeat_opponent_turn = True
                elif card.is_repeat:
                    self.repeat_opponent_turn = True

                if not self.opponent_cards and not self.opponent_has_called_noah:
                    self._apply_noah_penalty_opponent()

                    with self.game.repaint():
                        self.update_opponent_cards()
                    
                    CallAfter(lambda: self.game.player.play(f'noah{random.randint(1, 3)}'))

            return not self.opponent_cards, True
        
    def _opponent_turn(self) -> None:
        """Executes the opponent's AI turn, plays first valid card or draws a card."""

        if self.game_over or self.game.closed:
            return
        
        playable_cards = [card for card in self.opponent_cards if self.can_play(card, player=False)]

        chosen_card = None

        if playable_cards:
            chosen_card = self.get_most_effective_opponent_card(playable_cards)

            if chosen_card.type is CardType.WILD:
                chosen_colour = self.get_most_effective_opponent_colour(including_middle_cards=False)

                if TYPE_CHECKING:
                    assert self.middle_card is not None

                middle_card_colour = self.middle_card.colour
                chosen_card.set_wild_card_colour(
                    chosen_colour
                    or random.choice(
                        [
                            col
                            for col in COLOUR_MAPPING.values()
                            if col != middle_card_colour
                        ]
                    )
                )

        win, manual_repaint = False, True

        if chosen_card is None:
            self._opponent_draw()

            chosen_card = self.opponent_cards[-1]

            if self.can_play(chosen_card, player=False):
                if chosen_card.type is CardType.WILD:
                    chosen_colour = self.get_most_effective_opponent_colour(including_middle_cards=False)

                    chosen_card.set_wild_card_colour(chosen_colour or random.choice(list(COLOUR_MAPPING.values())))

                win, manual_repaint = self._opponent_play(chosen_card)
        else:
            win, manual_repaint = self._opponent_play(chosen_card)

        if manual_repaint:
            with self.game.repaint():
                self.update_opponent_cards()

        if win:
            self.finish(False)
        elif self.repeat_opponent_turn:
            self.repeat_opponent_turn = False

            CallLater(self.game.config.turn_timeout, self._opponent_turn)
        else:
            self.player_turn()

    def opponent_turn(self) -> None:
        """Signals an opponent turn."""

        self.is_opponent_turn = True

        self.pickup_card_stack_image.SetCursor(Cursor(CURSOR_NO_ENTRY))

        for child in self.player_card_sizer.GetChildren():
            child.GetWindow().SetCursor(Cursor(CURSOR_NO_ENTRY))

        CallLater(self.game.config.turn_timeout, self._opponent_turn)

    def reflect_theme(self) -> None:
        """Reflects the game session based on the game's theme."""

        if self.middle_card is not None:
            # UPDATE MIDDLE CARD (DISCARD PILE)
            self.middle_card_image.SetBitmap(BitmapBundle(self.middle_card.get_image((116, 168))))

        # UPDATE OPPONENT CARDS
        self.background_card_image = BitmapBundle(self.background_card.get_image((80, 120)))

        for column in self.opponent_card_columns:
            column.reflect_theme()

        # UPDATE THE PICKUP CARDS
        self.pickup_card_stack_image.SetBitmap(BitmapBundle(self.pickup_card.new_stack_image()))

        # UPDATE PLAYER CARDS
        background_colour = Brush(self.game.config.get_colour('bg_primary'))

        if self.player_cards:
            player_card_sizer_children = self.player_card_sizer.GetChildren()

            for i in range(0, self.player_card_column_count):
                image = self.player_card_columns[i]

                dc = MemoryDC(image)
                dc.SetBackground(background_colour)
                dc.Clear()

                gc = GraphicsContext.Create(dc)

                y = 0

                # PASTE THE CARDS WITH OFFSET
                for j in range(i,self.in_page_player_card_count, self.game.config.max_card_column_count,):
                    card = self.get_player_card(j)

                    new_image = card.get_image((80, 120))

                    if TYPE_CHECKING:
                        assert isinstance(new_image, Image)

                    gc.DrawBitmap(Bitmap(new_image), 0, y, 80, 120)

                    y += 35

                del dc

                player_card_sizer_children[i].GetWindow().SetBitmap(image)

        self.player_card_previous_image.SetBitmap(self.game.config.previous_image)
        self.player_card_next_image.SetBitmap(self.game.config.next_image)

        super().reflect_theme()

    def restore(self) -> None:
        """Recreates a new game session."""

        is_reload = self.middle_card is not None
        self.has_called_noah = False
        self.opponent_has_called_noah = False
        self.noah_button.Hide()

        # CREATE PLAYER/OPPONENT HANDS
        player_hand, opponent_hand = Card.new_hands(self.game.config.max_card_column_count)

        # RANDOM MIDDLE CARD (DISCARD PILE) FROM THE NUMBER CARDS
        self.middle_card = Card.new_middle(self.game.config)

        middle_card_image = BitmapBundle(self.middle_card.get_image((116, 168)))

        # OPPONENT CARDS, TOP OF SCREEN
        self.opponent_card_sizer = BoxSizer(HORIZONTAL)
        self.opponent_cards = [Card(self.game.config, key) for key in opponent_hand]

        for _ in opponent_hand:
            self.add_opponent_card_column()

        self.update_opponent_cards()

        # PLAYER CARDS, BOTTOM OF SCREEN
        self.player_card_columns = [Bitmap(80, 120) for _ in range(0, self.game.config.max_card_column_count)]
        self.player_cards = []
        self.player_card_sizer = BoxSizer(HORIZONTAL)

        for card in map(lambda key: Card(self.game.config, key), player_hand):
            self._draw(card)

        # SIZERS
        main_sizer = BoxSizer(VERTICAL)
        main_sizer.AddStretchSpacer()

        # OPPONENT CARDS
        main_sizer.Add(self.opponent_card_sizer, 0, ALIGN_CENTER | TOP)
        main_sizer.AddStretchSpacer()

        # MIDDLE CARD (DISCARD PILE)
        middle_card_sizer = BoxSizer(HORIZONTAL)
        middle_card_sizer.AddStretchSpacer()

        if is_reload:
            self.middle_card_image.SetBitmap(middle_card_image)
        else:
            self.middle_card_image = StaticBitmap(self.panel, bitmap=middle_card_image)

        safe_add_to_sizer(middle_card_sizer, self.middle_card_image, 0, ALL, 10)
        middle_card_sizer.AddSpacer(75)
        safe_add_to_sizer(middle_card_sizer, self.pickup_card_stack_image, 0, ALL, 10)

        main_sizer.Add(middle_card_sizer, 0, ALIGN_CENTER)
        main_sizer.AddStretchSpacer()

        # PLAYER CARDS
        self.stacked_card_count = 0
        self.is_opponent_turn = False
        self.repeat_opponent_turn = False
        self.player_card_page = 0
        self.update_player_cards()

        player_card_wrapper_sizer = BoxSizer(HORIZONTAL)

        safe_add_to_sizer(player_card_wrapper_sizer, self.player_card_previous_image, 0, ALIGN_CENTER)
        player_card_wrapper_sizer.AddSpacer(20)
        player_card_wrapper_sizer.Add(self.player_card_sizer, 0, ALIGN_CENTER)
        player_card_wrapper_sizer.AddSpacer(20)
        safe_add_to_sizer(player_card_wrapper_sizer, self.player_card_next_image, 0, ALIGN_CENTER)

        main_sizer.Add(player_card_wrapper_sizer, 0, ALIGN_CENTER | BOTTOM)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)
        self.game_over = False
        super().restore()

    def _on_resize(self, event) -> None:
        """Handles session resize event."""

        super()._on_resize(event)

        if self.noah_button.IsShown():
            self.position_noah_button()

    def cleanup(self) -> None:
        """Runs at the end of the game session panel's lifecycle."""

        self.is_opponent_turn = False
        self.has_called_noah = False
        self.opponent_has_called_noah = False
        self.noah_button.Hide()

        self.player_cards.clear()
        self.player_card_sizer.Clear(delete_windows=True)

        self.opponent_cards.clear()
        self.opponent_card_sizer.Clear(delete_windows=True)
        self.opponent_card_columns.clear()

        super().cleanup()

    def finish(self, player_is_winner: bool) -> None:
        """Finishes the game session."""

        record_win(player=player_is_winner)

        game_over = GameOver(self, player_won=player_is_winner)
        game_over.ShowModal()