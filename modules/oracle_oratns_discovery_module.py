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
module: oracle_oratns_discovery_module

short_description: This module discover oracle TNS data

version_added: "1.0"

description:
    - "This module discover oracle TNS data"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where RMAN binary resides (lack of parameter means it will be derived from /etc/oratab).
        required: false
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database
        required: false
    oratab_location:
        description:
            - Location of the oratab file (if not provided /etc/oratab will be used.
        required: false


'''

EXAMPLES = '''
# Execute discovery with all parameters
- name: Check TNS information
  oracle_oratns_discovery_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    oratab_location: '/var/tmp/oratab'

# Execute discovery with minimal set of parameters
- name: Check TNS information
  oracle_oratns_discovery_module:
    oracle_sid: '<SID>'
    
'''

RETURN = '''

oracle_home:
    description: 
    type: str

sqlnet_ora_encryption_wallet:
    description: 
    type: str

'''

from ansible.module_utils.basic import AnsibleModule
from subprocess import Popen, PIPE
from tempfile import mkstemp, TemporaryFile
from datetime import datetime, timedelta
import os, sys, re
import json


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

def find_sqlnet_ora_encryption_wallet(oracle_home):

    re_wallet_path = re.compile(r'DIRECTORY=(?P<WALLET_PATH_FILE>(/|\w+|\/)+)\)')

    with open(oracle_home+'/network/admin/sqlnet.ora', 'r') as f:
        for line in f:
            line = line.strip()
            re_wallet_path_match = re_wallet_path.search(line)
            if re_wallet_path_match:
                try:
                    wallet_path = re_wallet_path_match.group('WALLET_PATH_FILE')
                except Exception: 
                    wallet_path = ''
                return wallet_path
          

def execute_main(oracle_home, oracle_sid, oratab_location):

    if oracle_home is None: 
       oracle_home = find_oracle_home(oracle_sid, oratab_location)

    sqlnet_ora_encryption_wallet = find_sqlnet_ora_encryption_wallet(oracle_home)   

    return ['',oracle_home, sqlnet_ora_encryption_wallet]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        oracle_sid=dict(type='str', required=False),
        oratab_location=dict(type='str', required=False),                  
    )

    result = dict(
        changed=False,
        oracle_home='',
        sqlnet_ora_encryption_wallet='',

    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_main = execute_main(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['oratab_location'])
    
    result['oracle_home'] = results_of_execute_main[1]
    result['sqlnet_ora_encryption_wallet'] = results_of_execute_main[2]
    
     
    if results_of_execute_main[0] != '':
        module.fail_json(msg='Module has failed! ('+results_of_execute_main[0]+')', **result)  
       

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
