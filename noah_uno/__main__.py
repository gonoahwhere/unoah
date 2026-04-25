from .game import Game
from .utils.config import Config

game = Game(Config())
game.start()