import gym
from gym import spaces
import numpy as np
from .card_deck import Deck, Card
from .dealer import Dealer, FixedDealer
import config

class BlackjackEnv(gym.Env):
    """
    Custom OpenAI Gym Environment for Blackjack.
    Attributes:
        action_space: 0 (Stand), 1 (Hit)
        observation_space: Tuple of (Player Sum, Dealer Up Card, Usable Ace)
        Note: We can extend observation space for Learning Dealer scenarios.
    """
    
    def __init__(self, dealer: Dealer = None):
        super(BlackjackEnv, self).__init__()
        
        self.dealer = dealer if dealer else FixedDealer()
        self.deck = Deck(num_decks=config.DECK_COUNT)
        
        # Action space: 0 = Stand, 1 = Hit
        self.action_space = spaces.Discrete(2)
        
        # Observation space:
        # Player Sum: 4-21 (actually can go higher if bust, but we terminate) -> let's say 32 to be safe
        # Dealer Up Card: 2-11 (Ace=11)
        # Usable Ace: 0 or 1
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0]), 
            high=np.array([32, 11, 1]), 
            dtype=np.float32
        )
        
        self.player_hand = []
        self.reset()
        
    def reset(self):
        self.deck = Deck(num_decks=config.DECK_COUNT) # Optional: Reshuffle every ep or maintain deck?
        # Usually for RL training we assume fresh deck or standard shuffle to reduce variance,
        # but counting cards requires continuous deck. 
        # For simple Basic Strategy training, fresh deck is fine.
        # Let's keep the deck stateful but shuffle if low (handled in Deck class).
        
        self.dealer.reset()
        self.player_hand = []
        
        # Deal initial cards
        self.player_hand.append(self.deck.deal())
        self.dealer.add_card(self.deck.deal())
        self.player_hand.append(self.deck.deal())
        self.dealer.add_card(self.deck.deal())
        
        return self._get_obs()

    def _get_obs(self):
        player_value, usable_ace = self._calculate_hand(self.player_hand)
        dealer_up_card_val = self.dealer.up_card.value
        return np.array([player_value, dealer_up_card_val, int(usable_ace)], dtype=np.float32)

    def _calculate_hand(self, hand):
        value = 0
        aces = 0
        for card in hand:
            val = card.value
            if val == 11:
                aces += 1
            value += val
            
        while value > 21 and aces:
            value -= 10
            aces -= 1
            
        return value, (aces > 0)

    def _get_dealer_obs(self):
        dealer_val, dealer_ace = self._calculate_hand(self.dealer.hand)
        player_val, _ = self._calculate_hand(self.player_hand)
        return np.array([dealer_val, player_val, int(dealer_ace)], dtype=np.float32)

    def step(self, action):
        """
        Action: 0 = Stand, 1 = Hit
        """
        # Calculate current player value
        player_value, _ = self._calculate_hand(self.player_hand)
        
        if action == 1: # Hit
            self.player_hand.append(self.deck.deal())
            player_value, _ = self._calculate_hand(self.player_hand)
            
            if player_value > 21:
                return self._get_obs(), -1.0, True, {} # Bust
            else:
                return self._get_obs(), 0.0, False, {} # Continue
                
        else: # Stand
            # Dealer plays
            done = True
            
            # Dealer turn
            while True:
                dealer_val = self.dealer.get_hand_value()
                if dealer_val >= 21: # Dealer bust or 21
                    break
                
                # Ask dealer for action
                dealer_state = self._get_dealer_obs()
                dealer_action = self.dealer.get_action(dealer_state) 
                if dealer_action == 1:
                    self.dealer.add_card(self.deck.deal())
                else:
                    break
            
            dealer_value = self.dealer.get_hand_value()
            
            # Determine winner
            if dealer_value > 21:
                return self._get_obs(), 1.0, True, {} # Dealer bust, Player win
            elif dealer_value > player_value:
                return self._get_obs(), -1.0, True, {} # Dealer wins
            elif dealer_value < player_value:
                if player_value == 21 and len(self.player_hand) == 2:
                    return self._get_obs(), config.BLACKJACK_PAYOUT, True, {} # Blackjack
                return self._get_obs(), 1.0, True, {} # Player wins
            else:
                return self._get_obs(), 0.0, True, {} # Push
