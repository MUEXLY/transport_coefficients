import argparse
from string import Template
from random import randint

from config import get_config


CONFIG = get_config()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--composition",
        nargs="*",
        type=float
    )
    
    parser.add_argument(
        "--defect",
        type=str
    )
    
    parser.add_argument(
        "--temperature",
        type=int
    )
    
    args = parser.parse_args()
    
    current_composition = [0.0 for _ in args.composition]
    current_composition[CONFIG.borrowing_index] = 1.0
    
    num_types = len(args.composition)
    composition_lines = [f"set group all type {CONFIG.borrowing_index + 1}"]
    
    for i in range(num_types):
        if i == CONFIG.borrowing_index:
            continue
        composition_lines.append(
            f"set type {CONFIG.borrowing_index + 1} type/ratio {i + 1} {args.composition[i] / current_composition[CONFIG.borrowing_index]} {randint(0, 999999):.0f}"
        )
        # "steal" from element at first index, populate into element at index i
        current_composition[i] = args.composition[i]
        current_composition[CONFIG.borrowing_index] += -current_composition[i]
        
    d = {
        'ntypes': num_types,
        'pair_style': CONFIG.potential.pair_style,
        'pair_coeff': CONFIG.potential.pair_coeff,
        'defect': args.defect,
        'temperature': args.temperature,
        'composition_lines': '\n'.join(composition_lines)
    }
    
    with open('template.in', 'r') as file:

        src = Template(file.read())
        result = src.substitute(d)
    print(result)
    
    
if __name__ == '__main__':

    main()
