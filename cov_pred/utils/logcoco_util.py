import json

def get_validation_signatures(project, registry):
    validation_oracle_file = f"output/{project}_{registry}/method_level_validation_oracle.json"
    with open(validation_oracle_file, 'r') as f:
        validation_oracle = json.load(f)
    return list(validation_oracle.keys())
