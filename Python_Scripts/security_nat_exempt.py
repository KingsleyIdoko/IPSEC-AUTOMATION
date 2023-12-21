from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.nat_exempt import nat_policy
from xml.dom import minidom
from lxml import etree

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class DeviceConfigurator:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)
    def fetch_nat_data(self):
        nat_data = []
        sub_nat_rules = []
        nat_exempt_vpn_prefixes = []
        try:
            self.response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in self.response:
                result = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  self.response[nat].result['configuration']['security']['address-book'][1]['address']
                for subnet in remote_subnets:
                    nat_exempt_vpn_prefixes.append(subnet['ip-prefix'])
                nat_data.append(result['name'])
                nat_data.append(result['from']['zone'])
                nat_data.append(result['to']['zone'])
                for nat_rules in result['rule']:
                    sub_nat_rules.append(nat_rules['name'])
                print(sub_nat_rules)
                nat_rule_name = "rule" + str(len(sub_nat_rules)+1)
                nat_data.append(nat_rule_name)
                nat_data.append(nat_exempt_vpn_prefixes)
            return nat_data
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    def build_config(self):
        global_nat_rule, source_zone, destination_zone, rule_set, nat_exempt_vpn_prefixes = self.fetch_nat_data()
        payload = minidom.parseString(nat_policy(global_nat_rule, source_zone, destination_zone, rule_set, nat_exempt_vpn_prefixes))
        formatted_xml = payload.toprettyxml()
        formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
        return formatted_xml

    def push_config(self):
        payload = self.build_config()
        response = self.nr.run(task=pyez_config, payload=payload, data_format='xml')
        for res in response:
            diff_result = self.nr.run(task=pyez_diff)
            for res in diff_result:
                if diff_result[res].result is None:
                    print("No Config Change")
                    return
                print(diff_result[res].result)
                committed = self.nr.run(task=pyez_commit)
                for res1 in committed:
                    print(committed[res1].result)
config = DeviceConfigurator()
response = config.push_config()
