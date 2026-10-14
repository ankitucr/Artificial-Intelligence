from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from .card_deck import Card

if TYPE_CHECKING:
    from rl_agent.dqn_agent import DQNAgent

class Dealer(ABC):
    def __init__(self):
        self.hand: List[Card] = []

    def reset(self):
        self.hand = []

    def add_card(self, card: Card):
        self.hand.append(card)

    @property
    def up_card(self) -> Card:
        """Returns the dealer's visible card (usually the first one)."""
        if not self.hand:
            raise ValueError("Dealer has no cards!")
        return self.hand[0]

    def get_hand_value(self) -> int:
        """Calculates the value of the hand, handling Aces."""
        value = 0
        aces = 0
        for card in self.hand:
            val = card.value
            if val == 11:
                aces += 1
            value += val
        
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    @abstractmethod
    def get_action(self, state=None) -> int:
        """
        Returns the action: 0 for Stand, 1 for Hit.
        State can be passed for learning dealers.
        """
        pass

class FixedDealer(Dealer):
    def get_action(self, state=None) -> int:
        """
        Dealer hits on soft 17 or less, stands on hard 17 or more.
        Simplified: Hits if value < 17.
        """
        if self.get_hand_value() < 17:
            return 1 # Hit
        return 0 # Stand

class LearningDealer(Dealer):
    def __init__(self, agent=None):
        super().__init__()
        self.agent = agent

    def set_agent(self, agent):
        self.agent = agent

    def get_action(self, state=None) -> int:
        if self.agent is None:
            # Fallback to random or fixed if no agent set
            return 1 if self.get_hand_value() < 17 else 0
        
        # We assume state is provided by the environment in the format the agent expects
        # Or we construct it here. 
        # Typically the dealer sees its own hand value and maybe the player's info?
        # For simplicity, let's assume 'state' is passed correctly.
        if state is None:
             return 1 if self.get_hand_value() < 17 else 0
             
        return self.agent.select_action(state)
