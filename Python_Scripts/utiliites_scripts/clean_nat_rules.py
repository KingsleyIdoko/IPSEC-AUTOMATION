def compare_nat(payload):
    # Create a list to store the groups of rules
    collect_dup_rules = []

    # Loop through the payload list
    for i in range(len(payload)):
        # Get the first rule dictionary
        rule1 = payload[i]

        # Loop through the rest of the list
        for j in range(i + 1, len(payload)):
            # Get the second rule dictionary
            rule2 = payload[j]

            # Compare the source-address and destination-address values
            if (
                rule1['src-nat-rule-match'].get('source-address') == rule2['src-nat-rule-match'].get('source-address')
                and rule1['src-nat-rule-match'].get('destination-address') == rule2['src-nat-rule-match'].get('destination-address')
            ):
                # Append the names of the rules that have similar values to the list of groups
                collect_dup_rules.append([rule1['name'], rule2['name']])

    # Return the list of groups as the result
    return collect_dup_rules

def Rm_dup_rules(rules):
    # Create a new list to store the highest rules in each group
    highest_rules = []

    # Loop through the list of groups
    for group in rules:
        # Initialize the highest rule as the first element of the group
        highest_rule = group[0]

        # Loop through the rest of the group
        for rule in group[1:]:
            # Compare the rule names by removing the 'rule' prefix and converting to integers
            if int(rule[4:]) > int(highest_rule[4:]):
                # Update the highest rule if the current rule is higher
                highest_rule = rule

        # Append the highest rule to the new list
        highest_rules.append(highest_rule)

    # Return the new list as the result
    return highest_rules


def filter_list(payload):
    # Create a new list to store the items without duplicates
    list_without_duplicates = []

    # Loop through the original list
    for item in payload:
        # Check if the item is not in the new list
        if item not in list_without_duplicates:
            # Append the item to the new list
            list_without_duplicates.append(item)

    # Print the new list
    return list_without_duplicates


def nat_delete(rule):
    payload = f"""
            <configuration>
                <security>
                    <nat>
                        <source>
                            <rule-set>
                                <name>GLOBAL-NAT-RULE</name>
                                <rule operation="delete">
                                    <name>{rule}</name>
                                </rule>
                            </rule-set>
                        </source>
                    </nat>
                </security>
        </configuration>"""
    return payload


# Define a function to calculate the length of a prefix
def prefix_length(prefix):
    # Check if the prefix is None
    if prefix is None:
        # Return a default value, such as 0
        return 0
    # Otherwise, split the prefix by the slash
    parts = prefix.split('/')
    # If there is no slash, the length is 32
    if len(parts) == 1:
        return 32
    # Otherwise, the length is the number after the slash
    else:
        return int(parts[1])

def prefix_compare(prefix1, prefix2):
    # Check if the prefix1 is None
    if prefix1 is None:
        # Return a default value, such as 0
        num1 = 0
    # Otherwise, convert the prefix1 to an integer by removing the dots and slashes
    else:
        num1 = int(prefix1.replace('.', '').replace('/', ''))
    
    # Do the same for prefix2
    if prefix2 is None:
        num2 = 0
    else:
        num2 = int(prefix2.replace('.', '').replace('/', ''))

    # Compare the numerical values of the prefixes
    return num1 - num2

# Define a function to compare two nat rules
def rule_compare(rule1, rule2):
    # Get the source address and destination address of the rules
    src1 = rule1['src-nat-rule-match'].get('source-address')
    src2 = rule2['src-nat-rule-match'].get('source-address')
    dst1 = rule1['src-nat-rule-match'].get('destination-address')
    dst2 = rule2['src-nat-rule-match'].get('destination-address')
    # If the source addresses are lists, use the first element
    if isinstance(src1, list):
        src1 = src1[0]
    if isinstance(src2, list):
        src2 = src2[0]
    # If the destination addresses are lists, use the first element
    if isinstance(dst1, list):
        dst1 = dst1[0]
    if isinstance(dst2, list):
        dst2 = dst2[0]
    # Compare the source addresses using the prefix compare function
    src_cmp = prefix_compare(src1, src2)
    # If the source addresses are different, return the comparison result
    if src_cmp != 0:
        return src_cmp
    # Otherwise, compare the destination addresses using the prefix compare function
    dst_cmp = prefix_compare(dst1, dst2)
    # If the destination addresses are different, return the comparison result
    if dst_cmp != 0:
        return dst_cmp
    # Otherwise, compare the rule names
    else:
        return rule1['name'] < rule2['name']
    


# def re_order_nat_policy(zone_a, zone_b,closest_policies):
#     # Use a list to store the policy elements
#     policy_elements = []

 
#                 policy_element = f"""
#                          <policy insert="after"  key="[ name='{closest_policy}' ]" operation="merge">
#                             <name>{next_policy}</name>
#                          </policy>"""
#                 # Append the policy element to the list
#                 policy_elements.append(policy_element)
#     # Join the policy elements with a newline character
#     policy_elements = "\n".join(policy_elements)

#     # Create the payload with the policy elements
#     payload = f"""    
#         <configuration>
#                 <security>
#                     <nat>
#                         <source>
#                             <rule-set>
#                                 <name>GLOBAL-NAT-RULE</name>
#                                 <rule insert={first} operation="merge">
#                                   {policy_elements}
#                                 </rule>
#                             </rule-set>
#                         </source>
#                     </nat>
#                 </security>
#         </configuration>"""
    return payload


