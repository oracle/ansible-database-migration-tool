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
module: oracle_orapwd_module

short_description: This is simple ORAPWD module for remote execution

version_added: "1.0"

description:
    - "This module will help to setup Oracle database password file"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where RMAN binary resides (lack of parameter means it will be derived from /etc/oratab).
        required: false
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database
        required: true
    file:
        description:
            - This file will be create as database password file (if not declared will be constructed from ORACLE_HOME/dbs/orapwSID)
        required: false    
    password:
        description:
            - This password will be stored in database password file
        required: true  

'''

EXAMPLES = '''
# Execute ORAPWD remotely for FOGGYDB
- name: Create password file
  oracle_sqlplus_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    file: '/u01/app/oracle/product/12.1.0.2/dbhome_1/dbs/orapw<SID>'
    password: '<password>'

'''

RETURN = '''
orapwd_message:
    description: result ORAPWD execution.
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


def find_oracle_home(oracle_sid):

    re_db_home = re.compile(r'^('+oracle_sid+'):(?P<HOME>(/|\w+|\.)+):(Y|N)')

    with open('/etc/oratab', 'r') as f:
        for line in f:
            line = line.strip()
            re_db_home_match = re_db_home.search(line)
            if re_db_home_match:
                db_home = re_db_home_match.group('HOME')
                #print(db_home)

                return db_home

def execute_orapwd(oracle_home, oracle_sid, file, password):

    if oracle_home is None:
       oracle_home = find_oracle_home(oracle_sid)

    if file is None:
        file = oracle_home+"/dbs/orapw"+oracle_sid   

    args = [os.path.join(oracle_home, 'bin', 'orapwd')]
    args.append("password="+password)  
    args.append("file="+file)    
     
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)   

    stdoutResult, stderrResult = p.communicate()

    stdoutResult = stdoutResult.split('\n')
    stdoutResult[:] = [item for item in stdoutResult if item != '']

    return [' '.join(args), stdoutResult, stderrResult]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        oracle_sid=dict(type='str', required=True),
        file=dict(type='str', required=False),
        password=dict(type='str', required=True),
        
    )

    result = dict(
        changed=False,
        orapwd_message='',
        orapwd_command=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_orapwd = execute_orapwd(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['file'],
        module.params['password'],
        )
    
    result['orapwd_output'] = results_of_execute_orapwd[1]
    result['orapwd_command'] = results_of_execute_orapwd[0]
 
    if results_of_execute_orapwd[2] != '':
        module.fail_json(msg='ORAPWD module has failed!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
