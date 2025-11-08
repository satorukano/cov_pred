import json

def get_validation_signatures(project, registry, level):
    validation_oracle_file = ""
    if level == "method":
        validation_oracle_file = f"output/{project}_{registry}/method_level_validation_oracle.json"
    elif level == "line":
        validation_oracle_file = f"output/{project}_{registry}/validation_oracle.json"
    elif level == 'bulk':
        validation_oracle_file = f"output/{project}_{registry}/bulk_validation_oracle.json"
    with open(validation_oracle_file, 'r') as f:
        validation_oracle = json.load(f)
    return list(validation_oracle.keys())
