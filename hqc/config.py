import json
import os

#  Update config settings, or add new settings simply by accessing config.config
#  Example: (from another file) config.config['new_setting'] = 'setting'
#  Then update_config(config.config_json_filepath, config.config)

#  Config file location
config_json_filepath = "config.json"


def load_config(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config


def update_config(filename, config):
    with open(filename, 'w') as f:
        json.dump(config, f, indent=4)

#  Load json file upon startup
config = load_config(config_json_filepath)
