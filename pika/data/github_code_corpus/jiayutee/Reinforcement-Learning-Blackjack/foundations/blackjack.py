"""Teaching rules: replacement draws, hit/stand, S17, no natural bonus.

This is a plain Python environment, not yet a Gymnasium adapter.
The agent sees only (player total, dealer upcard, usable ace).
"""

import random
from typing import Sequence, Tuple

STAND = 0
HIT = 1
Observation = Tuple[int, int, bool]
# Ten, jack, queen, and king each occupy one of thirteen rank slots.
RANK_VALUES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10)


def score_hand(cards: Sequence[int]) -> Tuple[int, bool]:
    """Count aces as 1, then promote one to 11 when it does not bust."""
    total = sum(cards)
    usable_ace = 1 in cards and total + 10 <= 21
    return total + (10 if usable_ace else 0), usable_ace


class Blackjack:
    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)
        self._player = []
        self._dealer = []
        self._done = True

    def _draw(self) -> int:
        return self._rng.choice(RANK_VALUES)

    def _observation(self) -> Observation:
        total, usable_ace = score_hand(self._player)
        return total, self._dealer[0], usable_ace

    def reset(self) -> Observation:
        """Start a hand; continue the seeded random stream rather than reseeding."""
        self._player = [self._draw(), self._draw()]
        self._dealer = [self._draw(), self._draw()]
        self._done = False
        return self._observation()

    def visible_hand(self) -> dict:
        """Return a detached, JSON-ready view; reveal the dealer only at termination.

        These are card values, not ranks or suits. This is the Foundations profile.
        Never serialize the environment object itself for a browser.
        """
        if not self._player:
            raise RuntimeError("Call reset() before requesting a hand view.")
        player_total, usable_ace = score_hand(self._player)
        return {
            "rules": "foundations-v1: replacement draws, S17, no natural bonus, hit/stand",
            "player_cards": list(self._player),
            "player_total": player_total,
            "player_usable_ace": usable_ace,
            "dealer_cards": list(self._dealer) if self._done else [self._dealer[0], None],
            "dealer_total": score_hand(self._dealer)[0] if self._done else None,
            "done": self._done,
            "legal_actions": [] if self._done else [STAND, HIT],
        }

    def step(self, action: int) -> Tuple[Observation, float, bool]:
        """Return next observation, immediate reward, and episode termination."""
        if self._done:
            raise RuntimeError("Call reset() before acting on a new hand.")
        if type(action) is not int or action not in (STAND, HIT):
            raise ValueError("Action must be STAND (0) or HIT (1).")

        if action == HIT:
            self._player.append(self._draw())
            self._done = score_hand(self._player)[0] > 21
            return self._observation(), -1.0 if self._done else 0.0, self._done

        while score_hand(self._dealer)[0] < 17:
            self._dealer.append(self._draw())
        player_total = score_hand(self._player)[0]
        dealer_total = score_hand(self._dealer)[0]
        if dealer_total > 21 or player_total > dealer_total:
            reward = 1.0
        elif player_total < dealer_total:
            reward = -1.0
        else:
            reward = 0.0
        self._done = True
        return self._observation(), reward, True
