from yaml import safe_load


def read_config(path):
    with open(path, 'r') as f:
        config = safe_load(f)
    return config


config = read_config("config.yaml")


db_config = config['db']
encryption_config = config['Encrytion']