import csv
import json
import re
from urllib.request import urlopen
from io import StringIO
from typing import Dict

# Import existing skills
from skill_module_2136628898518373854 import levenshtein_distance

SAMPLE_ARGS = {
    "input_string": "example",
    "target_string": "example"
}

def run(args: Dict) -> Dict:
    input_string = args["input_string"]
    target_string = args["target_string"]
    
    distance = levenshtein_distance(input_string, target_string)
    
    return {
        "distance": distance
    }

if __name__ == '__main__':
    result = run(SAMPLE_ARGS)
    print(result)