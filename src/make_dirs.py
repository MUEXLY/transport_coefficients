import re
import argparse
from copy import deepcopy
from pathlib import Path
import os
from decimal import Decimal

from config import get_config


CONFIG = get_config()


def drange(x, y, jump):
    while x < y:
        yield float(x)
        x += jump


def main():

    p = argparse.ArgumentParser()
    p.add_argument("--start", nargs="*", type=Decimal)
    p.add_argument("--step", nargs="*", type=Decimal)
    p.add_argument("--end", nargs="*", type=Decimal)
    args = p.parse_args()

    assert len(args.start) == len(args.step) == len(args.end)

    midpoint = [(e + s) / 2 for e, s in zip(args.end, args.start)]
    midpoint[CONFIG.borrowing_index] = Decimal(1.0) - sum(midpoint[:CONFIG.borrowing_index]) - sum(midpoint[CONFIG.borrowing_index+1:])
    print(midpoint)
    compositions = set()

    for i, (start, step, end) in enumerate(zip(args.start, args.step, args.end)):
    
        if i == CONFIG.borrowing_index:
            continue
        
        for x in drange(start, end + step, step):
            composition = deepcopy(midpoint)
            composition[i] = Decimal(x)
            composition[CONFIG.borrowing_index] = Decimal(1.0) - sum(composition[:CONFIG.borrowing_index]) - sum(composition[CONFIG.borrowing_index+1:])
            composition = tuple(composition)
            assert 1.0 - CONFIG.epsilon <= sum(composition) <= 1.0 + CONFIG.epsilon
            if composition in compositions:
                continue
            compositions.add(composition)

    template = Path('src') / "template.pbs"
    with open(template, 'r') as file:
        template_lines = file.read()

    pattern = r'--composition\s+(?:\d+\.\d+\s+)+\d+\.\d+'

    for composition in compositions:

        new_dir = '_'.join((f'{100 * c:.0f}' for c in composition))
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        
        match = re.search(pattern, template_lines)
        if not match:
            raise ValueError
        
        new_composition_line = f"--composition {' '.join(f'{c}' for c in composition)}"
        new_content = re.sub(pattern, new_composition_line, template_lines)
        new_pbs_path = Path(f'{new_dir}/template.pbs')

        with open(new_pbs_path, 'w') as file:
            file.write(new_content)

        Path(f'{new_dir}/dump_files').mkdir(exist_ok=True)
        Path(f'{new_dir}/input_files').mkdir(exist_ok=True)
        Path(f'{new_dir}/log_files').mkdir(exist_ok=True)
        Path(f'{new_dir}/trash').mkdir(exist_ok=True)

        root = Path(os.getcwd())
        files_to_symlink = [
            "src/config.py",
            "src/input_file.py",
            "src/pbs_file.py",
            "src/submission.sh",
            "src/template.in",
            "config.json"
        ]

        for file in files_to_symlink + CONFIG.potential.files + [CONFIG.executable]:
            split = file.split("src/")
            file_absolute_name = split[-1]
            target_path = Path(f'{new_dir}/{file_absolute_name}')
            if target_path.is_symlink():
                target_path.unlink()
            target_path.symlink_to(root / file)

if __name__ == '__main__':
    main()
