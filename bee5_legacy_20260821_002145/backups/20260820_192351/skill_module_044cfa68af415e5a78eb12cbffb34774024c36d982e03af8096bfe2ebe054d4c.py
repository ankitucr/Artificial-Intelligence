# A micro-skill to summarize text using a basic neural network.
import numpy as np
import torch
class NeuralNetworkNode:
    def __init__(self):
        self.model = torch.nn.Linear(5, 3)
    def forward(self, x):
        return self.model(x)
