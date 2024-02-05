import yaml
import os

def loadFile():
    with open('config/config.yaml', mode='rt', encoding='utf-8')as file:
        configs = yaml.safe_load(file)
    return configs
