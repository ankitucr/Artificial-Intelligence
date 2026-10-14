import random
from typing import List, Tuple

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def __repr__(self):
        return f"Card({self.rank}, {self.suit})"

    @property
    def value(self) -> int:
        """Returns the value of the card. Aces return 11 (handling soft/hard is done in hand calculation)."""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)

class Deck:
    def __init__(self, num_decks: int = 1):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.reset()

    def reset(self):
        """Resets the deck with fresh cards and shuffles."""
        self.cards = []
        for _ in range(self.num_decks):
            for suit in self.suits:
                for rank in self.ranks:
                    self.cards.append(Card(rank, suit))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """Deals a single card. If deck is empty, resets and deals."""
        if not self.cards:
            self.reset()
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)
