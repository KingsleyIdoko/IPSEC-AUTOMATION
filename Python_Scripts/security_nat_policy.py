from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.nat_exempt import nat_policy, delete_default_rules, update_rule_names
from utiliites_scripts.clean_nat_rules import (rule_compare, first_duplicate_rule, nat_delete,
                                            re_order_nat_policy, compare_nat, filter_list)
from xml.dom import minidom
from lxml import etree
from functools import cmp_to_key
from utiliites_scripts.fetch_data import append_nat_data, Serialize_nat_data
from utiliites_scripts.commit import run_pyez_tasks

script_dir = os.path.dirname(os.path.realpath(__file__))

class DeviceConfigurator:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
        try:
            self.response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in self.response:
                result = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  self.response[nat].result['configuration']['security']['address-book'][1]['address']
                source_subnets =  self.response[nat].result['configuration']['security']['address-book'][0]['address']
                nat_data = append_nat_data(result, remote_subnets, source_subnets)
            return nat_data
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def build_config(self):
        global_nat_rule, source_zone, destination_zone, rule_name, rm_prefixes, source_subnets = self.fetch_nat_data()
        nat_type = {'off': None}
        payload = minidom.parseString(nat_policy(global_nat_rule, source_zone, destination_zone, rule_name, rm_prefixes, nat_type=nat_type))
        formatted_xml = payload.toprettyxml()
        formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
        return formatted_xml
    
    def nat_rule_re_order(self):
        list_of_policies = []
        self.response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in self.response:
            nat_rules = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']['rule']
            rule_set_name = self.response[nat].result['configuration']['security']['nat']['source']['rule-set'].get('name')
        sorted_nat_rules = sorted(nat_rules, key=cmp_to_key(rule_compare))
        try: 
            for item in sorted_nat_rules:
                list_of_policies.append(item['name'])
            payload = re_order_nat_policy(list_of_policies, rule_set_name)
        except Exception as e:
            print(f"An error has occured {e}")
        return payload, rule_set_name
    
    def delete_duplicate_rules(self):
        self.response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in self.response:
            nat_rules = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']['rule']
        sorted_nat_rules = sorted(nat_rules, key=cmp_to_key(rule_compare))
        grap_duplicate_rules = compare_nat(sorted_nat_rules)
        unique_rules = filter_list(grap_duplicate_rules)
        dup_rules = first_duplicate_rule(unique_rules)
        del_duplicates = [item for item in set (dup_rules)]
        return del_duplicates
    

    def rename_nat_rules(self):
        xml_data = []
        global_nat_rule, source_zone, destination_zone, *_ = self.fetch_nat_data()
        self.response = self.nr.run(task=pyez_get_config,  database=self.database)
        for nat in self.response:
            nat_rules = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']['rule']
        serialized_data = Serialize_nat_data(nat_rules)
        payload = update_rule_names(serialized_data)
        for rule, destination, source_address, nat_type in serialized_data:
            payload = minidom.parseString(nat_policy(global_nat_rule, source_zone, destination_zone, rule, destination, source_address, nat_type))
            formatted_xml = payload.toprettyxml()
            formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
            xml_data.append(formatted_xml)
        clean_nat_rule = delete_default_rules()
        xml_data.insert(0, clean_nat_rule)
        return xml_data


    def push_config(self):
        new_nat_policy = self.build_config()
        run_pyez_tasks(self, new_nat_policy, 'xml')     
        updated_nat_order, rule_set_name = self.nat_rule_re_order()
        run_pyez_tasks(self, updated_nat_order, 'xml')  
        duplicate_rules =  self.delete_duplicate_rules()
        for rule in duplicate_rules:
            payload = nat_delete(rule, rule_set_name)
            response, committed = run_pyez_tasks(self, payload, 'xml')
        new_nat_rule_names = self.rename_nat_rules()
        for xml_data in  new_nat_rule_names:
            run_pyez_tasks(self, xml_data, 'xml')  

config = DeviceConfigurator()
response = config.push_config()