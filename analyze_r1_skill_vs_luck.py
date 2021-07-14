import pandas as pd
import pydantic
import random
import statistics
import numpy as np

class Player(pydantic.BaseModel):
    elo: int
    points: int = 0
    games_played: int = 0


def make_player_pool(skill_dist: str="all_luck", skill_dist_params: dict = None, num_players: int=63) -> list[Player]:
    if skill_dist == "all_luck":
        elos = [1500] * num_players
    elif skill_dist  == "uniform":
        elos = np.linspace(skill_dist_params["min"], skill_dist_params["max"], num_players)
    return [Player(elo=elo) for elo in elos]


def play_game(players: list[Player]):
    # see https://stats.stackexchange.com/questions/63219/winning-probability-in-a-game-with-multiple-players
    elos = [player.elo for player in players]
    qs = [(idx, 10 ** (elo / 400)) for idx, elo in enumerate(elos)]

    rankings = []
    num_players = len(qs)
    while num_players > 0:
        winner_idx = random.choices(range(len(qs)), weights=list(zip(*qs))[1], k=1)[0]

        winning_player = players[qs[winner_idx][0]]
        winning_player.games_played += 1
        winning_player.points += (num_players * (num_players + 1)) / 2

        del qs[winner_idx]
        num_players = len(qs)
    

def simulate_round(players: list[Player], games_played=3, players_per_game=3): 
    while True:
        min_gp = min([p.games_played for p in players])
        players_with_min_gp = [p for p in players if p.games_played == min_gp]

        if min_gp == games_played or min_gp == games_played - 1 and len(players_with_min_gp) < players_per_game:
            break
        
        if len(players_with_min_gp) < players_per_game:
            players_with_one_above_min_gp = [p for p in players if p.games_played == min_gp + 1]
            sampled_players = players_with_min_gp + random.sample(players_with_one_above_min_gp, players_per_game - len(players_with_min_gp))
        else:
            sampled_players = random.sample(players_with_min_gp, k=3)

        play_game(sampled_players)


def simulate_n_rounds(name: str, create_player_pool, actual_stdev: float, N: int = 500):
    sds = []
    for i in range(N):
        players = create_player_pool()
        simulate_round(players)
        points_list = [player.points for player in players]
        std_dev = statistics.stdev(points_list)
        sds.append(std_dev)

    print(f"\nDistirbution of {name} SDs:")
    print(f"Min: {min(sds)}")
    print(f"Avg: {sum(sds) / len(sds)}")
    print(f"Max: {max(sds)}")
    actual_percentile = len([sd for sd in sds if sd < actual_stdev]) / len(sds)
    print(f"Percentile of Actual SD in all luck dist: {actual_percentile}")


def main():
    df = pd.read_csv("data/r1_standings.csv")
    df = df[~df["Name"].isna()]
    actual_points_list = df["TP"]
    actual_stdev = statistics.stdev(actual_points_list)
    print(f"Actual SD:\n{actual_stdev}")

    simulate_n_rounds("all luck", make_player_pool, actual_stdev)

    create_some_skill_players = lambda: make_player_pool(skill_dist="uniform", skill_dist_params={"min": 1400, "max": 1600})
    simulate_n_rounds("some skill", create_some_skill_players, actual_stdev)

    create_more_skill_players = lambda: make_player_pool(skill_dist="uniform", skill_dist_params={"min": 1200, "max": 1800})
    simulate_n_rounds("more skill", create_more_skill_players, actual_stdev)


if __name__ == "__main__":
    main()
