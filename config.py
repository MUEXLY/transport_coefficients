from json import load
from pathlib import Path
from dataclasses import dataclass
from typing import List


DEFAULT_PATH = Path("config.json")


@dataclass
class Potential:

    pair_style: str
    pair_coeff: str
    files: List[str]


@dataclass
class Configuration:

    executable: str
    potential: Potential
    borrowing_index: int
    epsilon: float
    


def get_config(config_path: Path = DEFAULT_PATH) -> dict:

    with open(config_path, "r") as file:
        config_dict = load(file)
        
    return Configuration(
        executable=config_dict["executable"],
        potential=Potential(**config_dict["potential"]),
        borrowing_index=config_dict["borrowing_index"],
        epsilon=config_dict["epsilon"]
    )
