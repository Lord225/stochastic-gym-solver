import itertools
import gymnasium as gym
from tqdm import tqdm
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from models import Model

def run_once(model: Model, env: gym.Env, max_steps: int, show_observation: bool, show_action: bool):    
    observation, _ = env.reset()
    fitness = 0.0

    for i in range(max_steps):
        action = model.make_decision(observation)
        observation, reward, terminated, truncated, _ = env.step(action)

        if show_observation:
            print(f"Observation: {observation}")
        if show_action:
            print(f"Action: {action}")

        fitness += float(reward)

        if terminated or truncated:
            return fitness, i+1
    return fitness, max_steps


def run_once_thin(model: Model, env: gym.Env, max_steps: int):    
    observation, _ = env.reset()
    fitness = 0.0

    for i in range(max_steps):
        observation, reward, terminated, truncated, _ = env.step(model.make_decision(observation))

        fitness += reward # type: ignore

        if terminated or truncated:
            return fitness, i+1
        
    return fitness, max_steps

def run_once_thin_wrapper(args):
    return run_once_thin(*args)

def run_batch(args):
    model, env, max_steps, batch_size = args
    
    return [run_once_thin(model, env, max_steps) for _ in range(batch_size)]


def run_simulation(models: list[Model]|Model, 
                   env: str|tuple[str, dict],
                   max_steps: int, 
                   repetitions: int = 1, 
                   batch_size = 100,
                   render: bool = False, 
                   show_observation: bool = False, 
                   show_action: bool = False,
                   ) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(models, list):
        models = [models]
        
    if isinstance(env, tuple):
        env, env_options = env
    else:
        env_options = {}

    if repetitions == 1:
        render_mode = "human" if render else None
        fitness, lenght = run_once(models[0], gym.make(env, render_mode=render_mode, **env_options), max_steps, show_observation, show_action)

        return np.array([fitness]), np.array([lenght])
    
    if (len(models) * repetitions) % batch_size != 0:
        raise ValueError(f"Batch size {batch_size} is not a multiple of the number of models {len(models) * repetitions}")
    
    batches = repetitions*len(models)//batch_size

    tasks = [
        (model, gym.make(env, **env_options), max_steps, batch_size)
        for model in itertools.islice(itertools.cycle(models), batches)
    ]

    with ProcessPoolExecutor() as executor:
        results = tqdm(executor.map(run_batch, tasks), total=batches)
        fitnesses, lengths = zip(*itertools.chain.from_iterable(results))
        return np.array(fitnesses).reshape(repetitions, len(models)), np.array(lengths).reshape(repetitions, len(models))


if __name__ == "__main__":
    from models import RandomModel
    import time
    models = [RandomModel() for _ in range(500)] # type: list[Model]

    start_time = time.time()
    fitness, lenghts = run_simulation(models, "LunarLander-v3", 150, repetitions=100, batch_size=50)
    end_time = time.time()

    print(f"Execution time: {end_time - start_time} seconds")

    print(fitness, lenghts)
    print(np.mean(fitness), np.mean(lenghts))

    # model = RandomModel()
    # fitness, lenght = run_simulation([model], "LunarLander-v3", 1000, 1, render=True, show_observation=True, show_action=True)
    # print(fitness, lenght)