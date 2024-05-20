import argparse
from string import Template

from config import get_config


CONFIG = get_config()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--temperature", type=int)
    parser.add_argument("--defect", type=str)
    args = parser.parse_args()
    
    d = {'t': args.temperature, 'd': args.defect, "PBS_O_WORKDIR": '${PBS_O_WORKDIR}', "executable": CONFIG.executable}
    
    with open('template.pbs', 'r') as file:
        src = Template(file.read())
        result = src.substitute(d)
        
    print(result)
    
    
if __name__ == '__main__':

    main()
