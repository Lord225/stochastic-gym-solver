import gymnasium as gym
import numpy as np
import argparse
import torch
import episode_runner
import tensorboardX
from models.nn_model import NeuralNetworkModel

def run_fitness(model, env: gym.Env, max_steps: int) -> float:
    observation, info = env.reset(seed=42)

    fitness = 0.0

    for i in range(max_steps):
        observation = torch.tensor(observation, dtype=torch.float32)
        action = model(observation)
        action = np.argmax(action.detach().numpy())
        observation, reward, terminated, truncated, _ = env.step(action)

        fitness += float(reward)

        if terminated or truncated:
            return fitness
        
    return fitness
def make_env():
    instance = gym.make("LunarLander-v3", continuous=False)
    
    return instance


def get_episode(resume: str):
    return int(resume.split("_")[-1].split(".")[0])

def main():
    TO_SCORE_PATH = "./retain"

    import os
    import tqdm

    values = []

    for model in tqdm.tqdm(os.listdir(TO_SCORE_PATH)):
        if model.endswith(".pth"):
            try:
                model_path = os.path.join(TO_SCORE_PATH, model)
                model = torch.load(model_path, weights_only=False)
                env = make_env()
                fitness = run_fitness(model, env, max_steps=1000)
                values.append((model_path, fitness, get_episode(model_path)))
            except Exception as e:
                print(f"Error with model {model}: {e}")
    import pandas as pd

    df = pd.DataFrame(values, columns=["model", "fitness", "episode"])

    df.to_csv("scores.csv")

if __name__ == "__main__":
    main()