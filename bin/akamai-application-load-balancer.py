#!/usr/local/bin/python3

# DISCLAIMER:
"""
This script is for demo purposes only which provides customers with programming information regarding the Developer APIs. This script is supplied "AS IS" without any warranties and support.

We assume no responsibility or liability for the use of the script, convey no license or title under any patent or copyright.

We reserve the right to make changes in the script without notification and make no representation or warranty that such application will be suitable for the specified use without further testing or modification.
"""

# HISTORY
"""
28/02/2018   -   Initial version.
03/07/2018   -   Added CLI tool compatible menus and functions. New feature to activate only based on loadid and version.

By Jaime Escalona
Akamai Solutions Architect

"""

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib
import argparse
from urllib.parse import urljoin



class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(0, '%s: error: %s\n' % (self.prog, message))


# Function to get the Load Balancing ID version active.
def load_id_version(get_active, loadid):
    request_version = session.get(urljoin(baseurl, '/cloudlets/api/v2/origins/currentActivations'))
    request_version = json.loads(request_version.text)
    try:
        version = str(request_version[loadid][get_active]['version'])
    except Exception as exc:
        version = 'null'
        print('ERROR: load balancing ID or active version(s) not found')
        pass
    return(version)


# Function to get the Load Balancing ID in Prod.
def get_load_version(version, loadid, verbose):
    request_balancing = session.get(urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/versions/' + version + '?validate=false'))
    request_balancing = json.loads(request_balancing.text)
    if verbose:
        print('DEBUG: API Endpoint:', urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/versions/' + version + '?validate=false'))
        print('DEBUG:',request_balancing,'\n')
    return(request_balancing)


# In the json response the data centers are under the same key, so this function indexes them in order to call them later on individually. This allows the user's data centers to ve provided in disorder and not necessarily to provide all of them.
def create_dc_index(balancing):
    dc_index = {}
    n = 0
    for entry in balancing['dataCenters']:
        # Building the index dictionary. Example: {'Alpharetta': 0, 'Dallas': 1, 'Fairfield': 2}
        dc_index[entry['originId']] = n
        n = n +1
    return(dc_index)


# Modify the json response stored in 'balancing' with the new % values for the data centers
def modify_datacenters(balancing, dc_index, my_datacenters):
    #my_datacenters = {'Dallas': 10.0, 'Fairfield': 30.0, 'Alpharetta': 60.0} 
    # Use the DC name and % value from the user's input
    try:
        for dc_name in my_datacenters.keys():
            dc_value = my_datacenters[dc_name]
            for entry in balancing['dataCenters']:
                # Look for the index number for the user's DC and use it to modify the correct DC in the 'balancing' variable which has the original json response
                dc_number = dc_index[dc_name]
                if entry['originId'] == dc_name:          
                    balancing['dataCenters'][dc_number]['percent'] = dc_value
                    print('INFO: DC', dc_name, 'Found and New weight set to', dc_value)
    except Exception as exc:
        print('ERROR: data center', dc_name, 'not found')
        balancing = 'dc_not_found'
        return(balancing)

    percentage_status = verify_percentage(balancing)
    if percentage_status is False:
        balancing = 'wrong_weights'
    return(balancing)


# Check the weights sum is always 100.0. This check is executed at this point once the request has been constructed with the user's weights because the script allows not all of the DCs to be specified.
def verify_percentage(balancing):
    weight_value = 0
    for dc_entry in balancing['dataCenters']:
        weight_value = weight_value + dc_entry['percent']
    if weight_value != 100.0:
        print('ERROR: weights sum =', weight_value)
        return(False)

    return(True)  


# This function can be used to further manipulate any parameters in the json object 'balancing' before sending the POST request to create a new version. For now only the description will be modified.
def update_params_balancing(balancing, version):
    balancing['description'] = 'INFO: cloned from version ' + version
    print(balancing['description'])
    return(balancing)


# Push the new weights to the new load id version
def push_change(balancing, loadid, verbose):
    print('INFO: uploading new version')
    headers = {'content-type': 'application/json'}
    # Convert the json object to a string that the API can interpret
    balancing = json.dumps(balancing)
    request_new = session.post(urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/versions'), data=balancing, headers=headers)
    # Pretty print
    #print(json.dumps(request_new.json(), indent=4, sort_keys=True))
    request_new = json.loads(request_new.text)
    if verbose:
        print('\nDEBUG: API Endpoint:', urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/versions'))
        print('DEBUG:',request_new,'\n')
    new_version = request_new['version']
    return(new_version)


# Activate load balancing ID
def activate_load_id(data, loadid, verbose):
    print('INFO: activating the new load balancing version')
    headers = {'content-type': 'application/json'}
    # Convert the json object to a string that the API can interpret
    version = data['version']
    data = json.dumps(data)

    request_activation = session.post(urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/activations'), data=data, headers=headers)

    if request_activation.status_code == 200:
        # Pretty print
        #print(json.dumps(request_activation.json(), indent=4, sort_keys=True))
        request_activation = json.loads(request_activation.text)
        if verbose:
            print('\nDEBUG: API Endpoint:', urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadid + '/activations'))
            print('DEBUG: ',request_activation,'\n')
        return()
    else:
        print('ERROR: load balancing ID', loadid, 'or version', str(version), 'not found')
        return()


# Get the policyId, property names and production version
def get_single_policy_associations(policyName, cloudletId):    
    response = session.get(urljoin(baseurl, '/cloudlets/api/v2/policies?cloudletId=' + cloudletId))
    response = json.loads(response.text)

    list_of_properties = []
    policyId=False
    for key in response:
        if key['name'] == policyName:
            policyId = str(key['policyId'])
            version = str(key['activations'][0]['policyInfo']['version'])

            for activations in key['activations']:
                list_of_properties.append(activations['propertyInfo']['name'])
   
    if policyId is False:
        print('Policy Not Found')
        exit()
    else:
        return(policyId, version, set(list_of_properties))


# Similar to the previous function, except this is global for all policyNames.
def get_all_policy_associations(cloudletId):    
    response = session.get(urljoin(baseurl, '/cloudlets/api/v2/policies?cloudletId=' + cloudletId))
    response = json.loads(response.text)

    list_of_properties = []
    policyId=False
    for key in response:

        policyName = key['name']
        policyId = str(key['policyId'])
    
        try:
            version = str(key['activations'][0]['policyInfo']['version'])
        except Exception as exc:
            version = 'null'
            pass

        for activations in key['activations']:
            list_of_properties.append(activations['propertyInfo']['name'])

        # Start building the dictionary: {PolicyName: [policyId, version, {properties}, {load balancing ids}]}
        d.setdefault(policyName, []).append(policyId)
        d.setdefault(policyName, []).append(version)    
        d.setdefault(policyName, []).append(list(set(list_of_properties)))
        list_of_properties = []

    if policyId is False:
        print('Policy Not Found')
        exit()
    else:
        return()


# Get the associated balancing Ids to a policyId/policyName
def get_associated_balancing_ids(policyId, version):
    response = session.get(urljoin(baseurl, '/cloudlets/api/v2/policies/' + policyId + '/versions/' + version))
    response = json.loads(response.text)

    list_of_balancing_ids = []

    if response['matchRules'] is not None:
        for rules in response['matchRules']:
            list_of_balancing_ids.append(rules['forwardSettings']['originId'])
        
        return(list_of_balancing_ids)
    else:
        return()


# Get all the associated balancing Ids using the partially built dictionary {PolicyName: [policyId, version, {properties}]}
def get_all_associated_balancing_ids():
    list_of_balancing_ids = []
    for policyName, content in d.items():
        policyId = content[0]
        version = content[1]
        # Check for policies that have no versions active and set those to null.
        if version == 'null':
            d.setdefault(policyName, []).append('null')
        else:
            list_of_balancing_ids = get_associated_balancing_ids(policyId, version)
            d.setdefault(policyName, []).append(list(set(list_of_balancing_ids)))
    return()


# Get the origins associated to the Load Balancing ID.
def get_associated_origins(loadbalancing_name):
    get_active = 'STAGING'
    list_of_origins = []

    version = load_id_version(get_active, loadbalancing_name)
    if version != 'null':
        response = session.get(urljoin(baseurl, '/cloudlets/api/v2/origins/' + loadbalancing_name + '/versions/' + version + '?validate=false'))
        response = json.loads(response.text)

        for dataCenter in response['dataCenters']:
            
            list_of_origins.append(dataCenter['originId'])

        return(list_of_origins)

    else:
        print('Policy Not Found')


# Print the properties, policies and load balancing Ids in a tree view.
def search_results_print(properties, policy, loadbalancing_ids):
    print('INFO: this is a tree view of the properties, policies, load IDs and origins associations')
    print('|--- Property\n    |--------- Policy\n              |------------ Load ID\n                           |------------ Origin\n') 

    for property_name in properties:
        print('|---',property_name)

    print('    |---------',policy)

    for loadbalancing_name in loadbalancing_ids:
        print('              |------------',loadbalancing_name) 

        origin_ids = get_associated_origins(loadbalancing_name)
        for origin_name in origin_ids:
            print('                           |------------',origin_name) 
    return()


# Initialization of section and edgerc.
def init_config(edgerc_file, section):
    global baseurl, session
    # Check if the edgerc_file variable or the AKAMAI_EDGERC env var exist then use a default value if they don't exist.
    if not edgerc_file:
        if not os.getenv("AKAMAI_EDGERC"):
            edgerc_file = os.path.join(os.path.expanduser("~"), '.edgerc')
        else:
            edgerc_file = os.getenv("AKAMAI_EDGERC")

    if not os.access(edgerc_file, os.R_OK):
        print("Unable to read edgerc file \"%s\"" % edgerc_file)
        exit(1)

    if not section:
        if not os.getenv("AKAMAI_EDGERC_SECTION"):
            section = "cloudlets"
        else:
            section = os.getenv("AKAMAI_EDGERC_SECTION")

    try:
        edgerc = EdgeRc(edgerc_file)
        baseurl = 'https://%s' % edgerc.get(section, 'host')

        session = requests.Session()
        session.auth = EdgeGridAuth.from_edgerc(edgerc, section)

        return(baseurl, session)

    except configparser.NoSectionError:
        print("Edgerc section \"%s\" not found" % section)
        exit(1)
    except Exception:
        print("Unknown error occurred trying to read edgerc file (%s)" % edgerc_file)
        exit(1)


# Main function
def main():
    global args

    parser = MyArgumentParser(
            description='Application Load Balancer Cloudlet Weitghts Updater', add_help=False
    )
    parser.add_argument('--version', action='version', version='ALB Cloudlet Weights Updater v2.0')

    subparsers = parser.add_subparsers(title='Commands', dest='command', metavar="")

    create_parser = subparsers.add_parser('help', help='Show available help').add_argument('args', metavar="", nargs=argparse.REMAINDER)
    parser_update = subparsers.add_parser('update', help='Modify target rule', add_help=False)
    parser_activate = subparsers.add_parser('activate', help='Activate a Load Balancing ID to Staging or Production', add_help=False)
    parser_search = subparsers.add_parser('search', help='Search for policies and load balancing IDs', add_help=False)

    mandatory_up = parser_update.add_argument_group('required arguments')
    mandatory_up.add_argument('--loadid', required=True, help='Load Balancing ID name')
    mandatory_up.add_argument('--datacenters', required=True, help='Data Center Name and Percentge Value, Example: \'DC1:20,DC2:35,DC3:45\'')
    
    optional_up = parser_update.add_argument_group('optional arguments')
    optional_up.add_argument('--stage', action='store_true', help='Work based on the last active verion in staging. By default the script works on the last version activated in production')
    optional_up.add_argument('--activate', choices={'STAGING', 'PRODUCTION'}, help='Activate the policy to the specified network. Default is PRODUCTION')
    optional_up.add_argument('--edgerc', help='Config file [default: ~/.edgerc]')
    optional_up.add_argument('--section', help='Config section in .edgerc [default: cloudlets]')
    optional_up.add_argument('--verbose', action='store_true', help='Enable verbose mode')

    mandatory_ac = parser_activate.add_argument_group('required arguments')
    mandatory_ac.add_argument('--loadid', required=True, help='Load Balancing ID name')
    mandatory_ac.add_argument('--version', required=True, help='Version of the Load Balancing ID to activate')

    optional_ac = parser_activate.add_argument_group('optional arguments')
    optional_ac.add_argument('--network', choices={'STAGING', 'PRODUCTION'}, help='Activate the policy to the specified network. Default is PRODUCTION')
    optional_ac.add_argument('--edgerc', help='Config file [default: ~/.edgerc]')
    optional_ac.add_argument('--section', help='Config section in .edgerc [default: cloudlets]')
    optional_ac.add_argument('--verbose', action='store_true', help='Enable verbose mode')

    mandatory_sr = parser_search.add_argument_group('required arguments')
    mandatory_sr.add_argument('--type', choices={'policy', 'loadid'}, required=True, help='Select to search for a policy or load balancing ID')
    mandatory_sr.add_argument('--name', required=True, help='Name to search for')

    optional_sr = parser_search.add_argument_group('optional arguments')
    optional_sr.add_argument('--edgerc', help='Config file [default: ~/.edgerc]')
    optional_sr.add_argument('--section', help='Config section in .edgerc [default: cloudlets]')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        return 0

    global baseurl, session

    if args.command == 'help':
        if len(args.args) > 0:
            if args.args[0] == 'update':
                parser_update.print_help()
        else:
            parser.print_help()
        return 0

    elif args.command == 'update':
       
        init_config(args.edgerc, args.section)

        # Process the DC/% input for later use
        dc_string = args.datacenters
        # Convert input DC/% string and convert it to a dictionary
        dc_string = dict(x.split(':') for x in dc_string.split(','))
        # Update the dictionary so that all values are float and not strings
        for dc_string_name, dc_string_value in dc_string.items():
            dc_string_value = float(dc_string_value)
            dc_string[dc_string_name] = dc_string_value

        # By default pull the information from the last version active in production.
        global get_active
        get_active = 'PRODUCTION'
        # If the -s option is used then use the last version active in staging.
        if args.stage:
            get_active = 'STAGING'

        print('\nINFO: getting the latest active version in', get_active)
        version = load_id_version(get_active, args.loadid)
        if version != 'null':
            balancing = get_load_version(version, args.loadid, args.verbose)
            index = create_dc_index(balancing)
            # Overwritting the origin json response with the new % values
            balancing = modify_datacenters(balancing, index, dc_string)
            
            if balancing == 'dc_not_found':
                print('ERROR: data center(s) not found')

            elif balancing == 'wrong_weights':
                print('ERROR: weights sum doesn\'t add to 100.0. Please check the weights.')

            else:
                if args.verbose:
                    print('\nDEBUG:',balancing,'\n')
                # Overwritting the json again to include description change
                balancing = update_params_balancing(balancing, version)
                push_version = push_change(balancing, args.loadid, args.verbose)
                print('INFO: new version is',push_version)

                if args.activate:
                    data = {'network': args.activate, 'originId': args.loadid, 'version': push_version}
                    activate_load_id(data, args.loadid, args.verbose)
                    return()

    elif args.command == 'activate':
        init_config(args.edgerc, args.section)
        data = {'network': args.network, 'originId': args.loadid, 'version': int(args.version)}
        activate_load_id(data, args.loadid, args.verbose)

    elif args.command == 'search':
        global d
        d = {}

        init_config(args.edgerc, args.section)

        if args.type == 'policy':
            print('\nINFO: searching for policy', args.name)
            # cloudletId=9 is for ALB
            policyId, version, list_of_properties = get_single_policy_associations(args.name, cloudletId='9')
            
            associated_balancing_ids = get_associated_balancing_ids(policyId, version)
            
            search_results_print(list_of_properties, args.name, associated_balancing_ids)


        elif args.type == 'loadid':
            print('\nINFO: searching for load balancing ID', args.name)
            get_all_policy_associations(cloudletId='9')
            get_all_associated_balancing_ids()

            # Search for the load balancing ID in the dictionary and display the associated policy and properties.
            notFound = True
            for policyName, content in d.items():
                list_of_balancing_ids = content[3]
                if type(list_of_balancing_ids) is list:
                    for balancing_id in list_of_balancing_ids:
                        if balancing_id == args.name:
                            notFound = False
                            search_results_print(content[2], policyName, list_of_balancing_ids)

            if notFound is True:
                print('ERROR: load balancing ID not found or has no associations')
        return()
            

# MAIN PROGRAM
if __name__ == "__main__":
    # Main Function
    main()