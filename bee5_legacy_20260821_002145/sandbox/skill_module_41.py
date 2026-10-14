import json
import yaml
import re
from typing import Dict
from datetime import datetime, timedelta

# Existing skills
def levenshtein_distance(s1: str, s2: str) -> int:
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1

    previous_row = list(range(len1 + 1))
    for i, c2 in enumerate(s2, 1):
        current_row = [i] + [0] * len1
        for j, c1 in enumerate(s1, 1):
            insertions = previous_row[j] + 1     
            deletions = current_row[j - 1] + 1    
            substitutions = previous_row[j - 1] + (c1 != c2)
            current_row[j] = min(insertions, deletions, substitutions)
        previous_row = current_row
    return previous_row[-1]

def parse_duration(duration: str) -> int:
    _UNIT_SECONDS = {
        "d": 86400,!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
        "h": 3600,   # hours
        "m": 60,     # minutes
        "s": 1       # seconds
    }
    if not isinstance(duration, str):
        raise TypeError("duration must be a string")
    total = 0
    pattern = re.compile(r"(?P<value>\d+)\s*(?P<unit>[dhmsDHMS])")
    for match in pattern.finditer(duration):
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _UNIT_SECONDS:
            raise ValueError(f"Unsupported time unit: {unit}")
        total += value * _UNIT_SECONDS[unit]
    if total == 0:
        raise ValueError(f"Could not parse duration string: '{duration}'")
    return total

def format_duration(seconds: int) -> str:
    if not isinstance(seconds, int):
        raise TypeError("seconds must be an integer")
    if seconds < 0:
        raise ValueError("seconds cannot be negative")
    parts = []
    remainder = seconds
    for unit, unit_sec in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if remainder >= unit_sec:
            qty, remainder = divmod(remainder, unit_sec)
            parts.append(f"{qty}{unit}")
    if not parts:
        return "0s"
    return " ".join(parts)

def camel_to_snake(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return snake

def snake_to_camel(name: str, capitalize_first: bool = True) -> str:
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    parts = name.split("_")
    if not parts:
        return ""
    if capitalize_first:
        return "".join(p.title() for p in parts)
    else:
        return parts[0] + "".join(p.title() for p in parts[1:])

def parse_yaml(yaml_str: str) -> Dict:
    try:
        return yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML: {e}")

def parse_json(json_str: str) -> Dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")

def build_pipeline(pipeline_config: Dict) -> Dict:
    pipeline = {}
    for stage in pipeline_config.get("stages", []):
        stage_name = stage.get("name")
        stage_type = stage.get("type")
        if stage_type == "source":
            pipeline[stage_name] = {
                "type": stage_type,
                "connector": stage.get("connector"),
                "config": stage.get("config")
            }
        elif stage_type == "transform":
            pipeline[stage_name] = {
                "type": stage_type,
                "script": stage.get("script"),
                "config": stage.get("config")
            }
        elif stage_type == "destination":
            pipeline[stage_name] = {
                "type": stage_type,
                "loader": stage.get("loader"),
                "config": stage.get("config")
            }
    return pipeline

def execute_pipeline(pipeline: Dict) -> Dict:
    execution_log = {}
    for stage_name, stage_config in pipeline.items():
        if stage_config["type"] == "source":
            # Execute source connector
            execution_log[stage_name] = {
                "status": "success",
                "output": "source_data"
            }
        elif stage_config["type"] == "transform":
            # Execute transformation script
            execution_log[stage_name] = {
                "status": "success",
                "output": "transformed_data"
            }
        elif stage_config["type"] == "destination":
            # Execute destination loader
            execution_log[stage_name] = {
                "status": "success",
                "output": "loaded_data"
            }
    return execution_log

def monitor_pipeline(execution_log: Dict) -> Dict:
    monitoring_log = {}
    for stage_name, stage_log in execution_log.items():
        if stage_log["status"] == "success":
            monitoring_log[stage_name] = {
                "status": "healthy",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            monitoring_log[stage_name] = {
                "status": "unhealthy",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    return monitoring_log

SAMPLE_ARGS = {
    "pipeline_config": """
    stages:
      - name: source
        type: source
        connector: mysql
        config:
          host: localhost
          port: 3306
          database: mydb
          username: myuser
          password: mypass
      - name: transform
        type: transform
        script: my_script.py
        config:
          input: source_data
          output: transformed_data
      - name: destination
        type: destination
        loader: postgres
        config:
          host: localhost
          port: 5432
          database: mydb
          username: myuser
          password: mypass
    """
}

def run(args: Dict) -> Dict:
    pipeline_config_str = args.get("pipeline_config", "")
    pipeline_config = parse_yaml(pipeline_config_str)
    pipeline = build_pipeline(pipeline_config)
    execution_log = execute_pipeline(pipeline)
    monitoring_log = monitor_pipeline(execution_log)
    return {
        "pipeline_config": pipeline_config,
        "execution_log": execution_log,
        "monitoring_log": monitoring_log
    }

if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    print(result)