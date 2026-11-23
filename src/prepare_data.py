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
assert len(team_stats) == 3356
assert team_stats.duplicated(team_keys).sum() == 0

matches["win"] = (matches["set_won"] == 3).astype(int)
matches["n_sets"] = matches.groupby(match_keys)["set_won"].transform("sum")
matches = matches[team_keys + ["team_name", "match", "competition_stage", "win", "n_sets"]]

team_matches = matches.merge(team_stats, on=team_keys, how="inner", validate="one_to_one")
assert len(team_matches) == 3356
assert team_matches.groupby(match_keys).size().eq(2).all()
assert team_matches.groupby(match_keys)["win"].sum().eq(1).all()

too_few_attacks = team_matches["att_tot"] / team_matches["n_sets"] < 10
bad_matches = team_matches.loc[too_few_attacks, match_keys].drop_duplicates()
team_matches = team_matches.merge(bad_matches, on=match_keys, how="left", indicator=True)
team_matches = team_matches[team_matches["_merge"] == "left_only"].drop(columns="_merge")
assert len(team_matches) == 3350
assert team_matches.groupby(match_keys).size().eq(2).all()

team_matches["ace_rate"] = team_matches["serv_pt"] / team_matches["serv_tot"]
team_matches["serve_error_rate"] = team_matches["serv_err"] / team_matches["serv_tot"]
team_matches["positive_reception_rate"] = team_matches["rec_pos_n"] / team_matches["rec_tot"]
team_matches["perfect_reception_rate"] = team_matches["rec_per_n"] / team_matches["rec_tot"]
team_matches["reception_error_rate"] = team_matches["rec_err"] / team_matches["rec_tot"]
team_matches["attack_kill_rate"] = team_matches["att_pt"] / team_matches["att_tot"]
team_matches["attack_error_rate"] = team_matches["att_err"] / team_matches["att_tot"]
team_matches["attack_blocked_rate"] = team_matches["att_blo"] / team_matches["att_tot"]
team_matches["attack_efficiency"] = (team_matches["att_pt"] - team_matches["att_err"] - team_matches["att_blo"]) / team_matches["att_tot"]
team_matches["blocks_per_set"] = team_matches["blo_pt"] / team_matches["n_sets"]

rate_cols = ["ace_rate", "serve_error_rate",
             "positive_reception_rate", "perfect_reception_rate", "reception_error_rate",
             "attack_kill_rate", "attack_error_rate", "attack_blocked_rate", "attack_efficiency",
             "blocks_per_set"]
assert team_matches[rate_cols].notna().all().all()

team_matches.to_csv(DATA / "team_matches.csv", index=False)


winners = team_matches[team_matches["win"] == 1]
losers = team_matches[team_matches["win"] == 0]

winners = winners[match_keys + ["competition_stage", "n_sets", "team_name", "match"] + rate_cols]
losers = losers[match_keys + ["team_name", "match"] + rate_cols]

match_pairs = winners.merge(losers, on=match_keys, suffixes=("_w", "_l"), validate="one_to_one")
assert len(match_pairs) == 1675
assert match_pairs.duplicated(match_keys).sum() == 0

for col in rate_cols:
    match_pairs[col + "_diff"] = match_pairs[col + "_w"] - match_pairs[col + "_l"]

match_pairs.to_csv(DATA / "match_pairs.csv", index=False)