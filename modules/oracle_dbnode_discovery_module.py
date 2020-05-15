#!/usr/bin/python
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: oracle_dbnode_discovery_module

short_description: This module discover oracle dbnode data

version_added: "1.0"

description:
    - "This module discover oracle dbnode data"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where RMAN binary resides (lack of parameter means it will be derived from /etc/oratab).
        required: false
    oracle_gi_home:
        description:
            - This is $ORACLE_HOME for GI.
        required: false    
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database
        required: false
    oratab_location:
        description:
            - Location of the oratab file (if not provided /etc/oratab will be used.
        required: false
    accept_data_not_found:
        description:
            - Accept some data cannot be found. 
        required: false        


'''

EXAMPLES = '''
# Execute discovery with all parameters
- name: Check open mode of database
  oracle_dbnode_discovery_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    oratab_location: '/var/tmp/oratab'

# Execute discovery with minimal set of parameters
- name: Check open mode of database
  oracle_dbnode_discovery_module:
    oracle_sid: 'FOGGYDB'
    
'''

RETURN = '''
oracle_home:
    description: ORACLE_HOME for delivered ORACLE_SID on start (according to oratab file)
    type: str
oracle_gi_home:
    description: Oracle Grid Infrastructure HOME
    type: str
local_listener_name:
    description: Local Listener Name
    type: str
local_listener_port:
    description: Local Listener Port
    type: str
listener_config_file:
    description: Listener Config File 
    type: str
scan_listener1:
    description: Scan Listener1 Name
    type: str
scan_listener2:
    description: Scan Listener2 Name
    type: str
scan_listener3:
    description: Scan Listener3 Name
    type: str
scan_listener_port:
    description: Scan listeners port
    type: str
scan_dns_name:
    description: Scan DNS Name
    type: str
changed:
    description: will be used for the future all removed.
    type: bool   
'''

from ansible.module_utils.basic import AnsibleModule
from subprocess import Popen, PIPE
from tempfile import mkstemp, TemporaryFile
from datetime import datetime, timedelta
import os, sys, re
import json


def demote(user_uid, user_gid):

    def set_ids():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return set_ids

def find_oracle_home(oracle_sid, oratab_location):

    if oratab_location is None:
        oratab_location = '/etc/oratab'

    re_db_home = re.compile(r'^('+oracle_sid+'):(?P<HOME>(/|\w+|\.)+):(Y|N)')

    with open(oratab_location, 'r') as f:
        for line in f:
            line = line.strip()
            re_db_home_match = re_db_home.search(line)
            if re_db_home_match:
                try:
                    db_home = re_db_home_match.group('HOME')
                except Exception: 
                    db_home = ''
                return db_home

def find_oracle_gi_home(oratab_location):

    if oratab_location is None:
        oratab_location = '/etc/oratab'

    re_gi_home = re.compile(r'(\+ASM[1-9]):(?P<HOME>(/|\w+|\.)+):(Y|N)')

    with open(oratab_location, 'r') as f:
        for line in f:
            line = line.strip()
            re_gi_home_match = re_gi_home.search(line)
            if re_gi_home_match:
                try:
                    gi_home = re_gi_home_match.group('HOME')
                except Exception: 
                    gi_home = ''
                return gi_home

def find_listener_name(oracle_gi_home):

    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('listener')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_listener_name = re.compile(r'^Name: (?P<LISTENER_NAME>(/|\w+|\.)+)')
        re_listener_name_match = re_listener_name.search(stdoutResult)
        try:
            local_listener_name = re_listener_name_match.group('LISTENER_NAME')
        except Exception: 
            local_listener_name = 'Error='+stdoutResult
        return local_listener_name

def find_listener_port(oracle_gi_home):
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('listener')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_listener_port = re.compile(r'End points: TCP:(?P<LISTENER_PORT>(/|\w+|\.)+)')
        re_listener_port_match = re_listener_port.search(stdoutResult)
        try:
            local_listener_port = re_listener_port_match.group('LISTENER_PORT')
        except Exception: 
            local_listener_port = ''
        return local_listener_port

def find_listener_config_file(oracle_home):
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    
    args = [os.path.join(oracle_home, 'bin', 'lsnrctl')]
    args.append('status')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_listener_config_file = re.compile(r'Listener Parameter File   (?P<LISTENER_CONFIG_FILE>(/|\w+|\.)+)')
        re_listener_config_file_match = re_listener_config_file.search(stdoutResult)
        try:
            listener_config_file = re_listener_config_file_match.group('LISTENER_CONFIG_FILE')
        except Exception: 
            listener_config_file = ''
        return listener_config_file


def find_scan_listeners(oracle_gi_home):
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('scan_listener')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        scan_listeners = []
        if oracle_gi_home == '/u01/app/19.0.0.0/grid':
            re_scan_listeners = re.compile(r'SCAN Listener (?P<SCAN_LISTENER>(/|\w+|\.)+) exists')
        else:    
            re_scan_listeners = re.compile(r'SCAN Listener (?P<SCAN_LISTENER>(/|\w+|\.)+) exists\.')
        try:
            for m in re_scan_listeners.finditer(stdoutResult):
                scan_listeners.append(m.group('SCAN_LISTENER'))
        except Exception: 
            scan_listeners = []
        return scan_listeners

def find_scan_listener_port(oracle_gi_home):
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('scan_listener')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        if oracle_gi_home == '/u01/app/19.0.0.0/grid':
            re_scan_listener_port = re.compile(r'Endpoints: TCP:(?P<SCAN_LISTENER_PORT>(/|\w+|\.)+)')
        else:
            re_scan_listener_port = re.compile(r'Port: TCP:(?P<SCAN_LISTENER_PORT>(/|\w+|\.)+)')

        re_scan_listener_port_match = re_scan_listener_port.search(stdoutResult)
        try:
            scan_listener_port = re_scan_listener_port_match.group('SCAN_LISTENER_PORT')
        except Exception: 
            scan_listener_port = ''
        return scan_listener_port        

def find_scan_dns_name(oracle_gi_home):
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('scan')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_scan_dns_name = re.compile(r'SCAN name: (?P<SCAN_DNS_NAME>(/|\w+|\.|\d|\-)+)')
        re_scan_dns_name_match = re_scan_dns_name.search(stdoutResult)
        try:
            scan_dns_name = re_scan_dns_name_match.group('SCAN_DNS_NAME')
        except Exception: 
            scan_dns_name = ''
        return scan_dns_name       

def find_dns_domain(oracle_gi_home):
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'srvctl')]
    args.append('config')
    args.append('scan')
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_dns_domain = re.compile(r'SCAN name: (/|\w+|\d|\-)+[.](?P<DNS_DOMIAN>(/|\w+|\.|\d|\-)+)')
        re_dns_domain_match = re_dns_domain.search(stdoutResult)
        try:
            dns_domain = re_dns_domain_match.group('DNS_DOMIAN')
        except Exception: 
            dns_domain = ''
        return dns_domain                  

def execute_main(oracle_home, oracle_gi_home, oracle_sid, oratab_location, accept_data_not_found):


    listener_config_file = ''

    if oracle_sid is None and accept_data_not_found is False:
        return ['ERROR: No ORACLE_SID defined when accept_data_not_found = False.', '','','','','','','','','','']

    if oracle_home is None and oracle_sid is not None: 
       oracle_home = find_oracle_home(oracle_sid, oratab_location)

       if oracle_home is None:
            if accept_data_not_found is False:
                return ['ERROR: File oratab not found or no ORACLE_SID within oratab file.', oracle_home,'','','','','','','','','']
       else:
            listener_config_file = find_listener_config_file(oracle_home)
            if listener_config_file == '':
                if accept_data_not_found is False:    
                    return ['ERROR: Error on executing lsnrctl status for listener config file.',oracle_home,'','','','','','','','',''] 
    
    if oracle_gi_home is None: 
        oracle_gi_home = find_oracle_gi_home(oratab_location)
    
    if oracle_gi_home is None and accept_data_not_found is False:
        return ['ERROR: File oratab not found or no ASM instance within oratab file.', oracle_home,'','','','','','','','','']

    if oracle_gi_home is None and accept_data_not_found is True:
        return ['',oracle_home, '', '', '', listener_config_file, '', '', '', '', '', ''] 

    local_listener_name = find_listener_name(oracle_gi_home)

    if local_listener_name == '':
        return ['ERROR: Error on executing srvctl config listener for local listener name.',oracle_home, oracle_gi_home,'','','','','','','','','']

    local_listener_port = find_listener_port(oracle_gi_home)

    if local_listener_port == '':
        return ['ERROR: Error on executing srvctl config listener for local listener port.',oracle_home, oracle_gi_home, local_listener_name,'','','','','','','','']

    scan_listeners = find_scan_listeners(oracle_gi_home)

    if scan_listeners == []:
        return ['ERROR: Error on executing srvctl config scan_listener for scan listeners.',oracle_home, oracle_gi_home, local_listener_name,'','','','','','','','']

    scan_listener_port = find_scan_listener_port(oracle_gi_home)    

    if scan_listener_port == '':
        return ['ERROR: Error on executing srvctl config scan_listener for scan listener port.',oracle_home, oracle_gi_home, local_listener_name, local_listener_port,listener_config_file, scan_listeners[0], scan_listeners[1], scan_listeners[2],'','','']

    scan_dns_name = find_scan_dns_name(oracle_gi_home)    

    if scan_dns_name == '':
        return ['ERROR: Error on executing srvctl config scan for scan dns name.',oracle_home, oracle_gi_home, local_listener_name, local_listener_port,listener_config_file, scan_listeners[0], scan_listeners[1], scan_listeners[2],scan_listener_port,'','']

    dns_domain = find_dns_domain(oracle_gi_home)    

    if dns_domain == '':
        return ['ERROR: Error on executing srvctl config scan for dns domain.',oracle_home, oracle_gi_home, local_listener_name, local_listener_port, listener_config_file, scan_listeners[0], scan_listeners[1], scan_listeners[2], scan_listener_port,'','']

    if oracle_home is None: 
        oracle_home = ''

    return ['',oracle_home, oracle_gi_home, local_listener_name, local_listener_port, listener_config_file, scan_listeners[0], scan_listeners[1], scan_listeners[2], scan_listener_port, scan_dns_name, dns_domain]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        oracle_gi_home=dict(type='str', required=False),
        oracle_sid=dict(type='str', required=False),
        oratab_location=dict(type='str', required=False),  
        accept_data_not_found=dict(type='bool', required=False, default=True),                 
    )

    result = dict(
        changed=False,
        oracle_home='',
        oracle_gi_home='',
        local_listener_name='',
        local_listener_port='',
        listener_config_file='',
        scan_listener1='',
        scan_listener2='',
        scan_listener3='',
        scan_listener_port='',
        scan_dns_name='',
        dns_domain='',

    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_main = execute_main(module.params['oracle_home'],module.params['oracle_gi_home'],module.params['oracle_sid'],module.params['oratab_location'],module.params['accept_data_not_found'])
    
    result['oracle_home'] = results_of_execute_main[1]
    result['oracle_gi_home'] = results_of_execute_main[2]
    result['local_listener_name'] = results_of_execute_main[3]
    result['local_listener_port'] = results_of_execute_main[4]
    result['listener_config_file'] = results_of_execute_main[5]
    result['scan_listener1'] = results_of_execute_main[6]
    result['scan_listener2'] = results_of_execute_main[7]
    result['scan_listener3'] = results_of_execute_main[8]
    result['scan_listener_port'] = results_of_execute_main[9]
    result['scan_dns_name'] = results_of_execute_main[10]
    result['dns_domain'] = results_of_execute_main[11]
    
    if results_of_execute_main[0] != '':
        module.fail_json(msg='Module has failed! ('+results_of_execute_main[0]+')', **result)  
       

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
