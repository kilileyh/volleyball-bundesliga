from pathlib import Path
import pandas as pd

ROOT = Path.cwd() if (Path.cwd() / "data").exists() else Path.cwd().parent
DATA = ROOT / "data" / "processed"

match_keys = ["season_id", "league_gender", "match_id"]
team_keys = match_keys + ["team_id"]
player_keys = team_keys + ["player_id"]

matches = pd.read_csv(DATA / "matches.csv")
matchstats = pd.read_csv(DATA / "matchstats.csv")


matchstats = matchstats.drop_duplicates(subset=player_keys)
assert matchstats.duplicated(player_keys).sum() == 0

matchstats = matchstats.drop(columns=["vote"])
matchstats["rec_pos_n"] = (matchstats["rec_tot"] * matchstats["rec_pos"] / 100).round()
matchstats["rec_per_n"] = (matchstats["rec_tot"] * matchstats["rec_per"] / 100).round()


count_cols = ["serv_tot", "serv_err", "serv_pt",
              "rec_tot", "rec_err", "rec_pos_n", "rec_per_n",
              "att_tot", "att_err", "att_blo", "att_pt",
              "blo_pt"]

team_stats = matchstats.groupby(team_keys)[count_cols].sum().reset_index()
print(team_stats)
assert len(team_stats) == 3356
assert team_stats.duplicated(team_keys).sum() == 0