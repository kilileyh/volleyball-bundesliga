from pathlib import Path
import pyreadr

Path("data/processed").mkdir(parents=True, exist_ok=True)

for name in ["matches", "matchstats", "players", "sets"]:
    result = pyreadr.read_r(f"data/raw/{name}.rda")
    df = result[name]
    df.to_csv(f"data/processed/{name}.csv", index=False)
    print(name, df.shape)
