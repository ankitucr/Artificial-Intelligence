import argparse
import torch
import numpy as np
import config
from environment import BlackjackEnv
from environment.dealer import FixedDealer, LearningDealer
from rl_agent.dqn_agent import DQNAgent
from training.evaluation import evaluate

def benchmark(player_model_path, num_games=1000):
    print(f"Benchmarking agent from {player_model_path} over {num_games} games...")
    
    # Initialize Environment
    env = BlackjackEnv(dealer=FixedDealer())
    input_size = env.observation_space.shape[0]
    output_size = env.action_space.n
    
    # Load Agent
    agent = DQNAgent(input_size, output_size)
    try:
        agent.load(player_model_path)
    except FileNotFoundError:
        print(f"Error: Model file '{player_model_path}' not found.")
        return

    # Use the evaluate function we already wrote
    win_rate, avg_reward, (wins, losses, pushes) = evaluate(agent, num_games, env)
    
    print("-" * 30)
    print(f"Results over {num_games} games:")
    print(f"Win Rate: {win_rate*100:.2f}%")
    print(f"Avg Reward: {avg_reward:.4f}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Pushes: {pushes}")
    print("-" * 30)

    # Calculate 'House Edge' equivalent (approximate)
    # If 1 unit bet, Average Reward approximates the expected return per hand.
    # House edge = -Expected Return (usually)
    print(f"Estimated Player Edge: {avg_reward*100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Benchmark Blackjack Agent')
    parser.add_argument('--model', type=str, required=True, help='Path to player model')
    parser.add_argument('--games', type=int, default=10000, help='Number of games to simulate')
    
    args = parser.parse_args()
    benchmark(args.model, args.games)
