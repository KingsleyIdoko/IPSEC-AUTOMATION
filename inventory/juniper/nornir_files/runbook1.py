from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

nr = InitNornir(config_file=f"{script_dir}/config.yml")

response = nr.run(
    task=pyez_get_config
)

# response is an AggregatedResult, which behaves like a list
# there is a response object for each device in inventory
devices = []
for dev in response:
    print(response[dev].result)