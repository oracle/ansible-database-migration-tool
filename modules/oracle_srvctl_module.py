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
module: oracle_srvctl_module

short_description: This is simple SRVCTL module for remote execution

version_added: "1.0"

description:
    - "This module will help to pickup some answers from SRVCTL exectution"

options:
    oracle_home:
        description:
            - Here you deliver Oracle Home name
        required: false
    add_oh_to_command:
        description:
            - No OH included in SRVCTL command.
        required: false        
    oracle_database:
        description:
            - Here you deliver database name
        required: false
    oracle_unqname:
        description:
            - Here you deliver Oracle Unique Name.
        required: false    
    oracle_instance:
        description:
            - Here you deliver instance name
        required: false 
    oracle_node:
        description:
            - Here you deliver node name
        required: false    
    srvctl_command:
        description:
            - What command will be executed.
        required: true               
    no_execution:
        description:
            - Show show the command which will be executed.
        required: false
    no_prompt:
        description:
            - No prompt option for removal.
        required: false
    force:
        description:
            - Force option for removal.
        required: false
    ignore_errors:
        description:
            - When set to True module will ignore ORA-XXXX errors 
        required: false
    os_env:
        description:
            - setenv options is used
        required: false   
    syntax_11g:
        description:
            - Oracle 11g syntax
        required: false   
                
'''

EXAMPLES = '''
# Execute SRVCTL remotely
- name: Create database with SRVCTL usage
  oracle_srvctl_module:
    grid_home: '/u01/app/12.2.0.1/grid'
    srvctl_command: 'add database'
    oracle_database: '<SID>'
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    
'''

RETURN = '''
srvctl_message:
    description: result of SRVCTL execution.
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

def execute_srvctl(oracle_home, add_oh_to_command, oracle_unqname, oracle_database, oracle_instance, oracle_node, srvctl_command, no_execution, no_prompt, force, ignore_errors, os_env, syntax_11g, detail):

    args = [os.path.join(oracle_home, 'bin', 'srvctl')]
    
    srvctl_command_list = srvctl_command.split()
    args.append(srvctl_command_list[0])
    args.append(srvctl_command_list[1])

    if oracle_home is not None:
        if add_oh_to_command is True:
            if syntax_11g is True:
                args.append('-o')
            else:    
                args.append('-oraclehome')
            args.append(oracle_home)

    if oracle_node is not None:
        if syntax_11g is True:
            args.append('-n')
        else:    
            args.append('-node')
        args.append(oracle_node)

    if oracle_instance is not None:
        if syntax_11g is True:
            args.append('-i')
        else:
            args.append('-instance')
        args.append(oracle_instance)

    if oracle_database is not None:
        if syntax_11g is True:
            if oracle_unqname is None:
                args.append('-d')
                args.append(oracle_database)
        else:
            args.append('-db')
            args.append(oracle_database)   

    if oracle_unqname is not None:
        if syntax_11g is True:
            args.append('-d')
            args.append(oracle_database)      
    
    if no_prompt is not None:
        if no_prompt is True:
            if syntax_11g is True:
                args.append('-y')
            else:
                args.append('-noprompt')

    if force is not None:
        if force is True:
            if syntax_11g is True:
                args.append('-f')
            else:
                args.append('-force')


    if os_env is not None:
        if syntax_11g is True:
            args.append('-T')
            args.append('"'+os_env+'')
        else:        
            args.append('-env')
            args.append('"'+os_env+'')

    if detail:
        args.append('-detail')        
            
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + ':'+oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    if oracle_database is not None:
        my_env["ORACLE_SID"] = oracle_database
    my_env["LD_LIBRARY_PATH="] = oracle_home+'/lib'
    
    if oracle_node is not None:
        my_env["HOSTNAME"] = oracle_node

    #if oracle_unqname is not None:
    #    my_env["ORACLE_UNQNAME"] = oracle_unqname
    #else:    
    #    my_env["ORACLE_UNQNAME"] = oracle_database
 
    if no_execution is True:
        return ['','','',' '.join(args),'']
    else:    
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
        
        srvctlResult, stderrResult = p.communicate()

        if srvctlResult.count('PRKO-') > 0:
            if ignore_errors == False: 
                oraErrors = re.findall('PRKO-(.+?):', srvctlResult) 
            else:
                oraErrors = '' 
        else:
            oraErrors = ''         

        if srvctlResult.count('PRCD-') > 0:
            if ignore_errors == False: 
                oraErrors = re.findall('PRCD-(.+?):', srvctlResult) 
            else:
                oraErrors = ''
        else:
            oraErrors = ''            

        if srvctlResult.count('PRCT-') > 0:
            if ignore_errors == False: 
                oraErrors = re.findall('PRCT-(.+?):', srvctlResult) 
            else:
                oraErrors = ''
        else:
            oraErrors = ''              

        srvctlResult = srvctlResult.split('\n')
        srvctlResult[:] = [item for item in srvctlResult if item != '']

        return [srvctlResult,oraErrors,stderrResult,' '.join(args), my_env]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        add_oh_to_command=dict(type='bool', required=False, default=False),
        oracle_unqname=dict(type='str', required=False),
        oracle_database=dict(type='str', required=False),
        oracle_instance=dict(type='str', required=False),
        oracle_node=dict(type='str', required=False),
        srvctl_command=dict(type='str', required=False),
        no_execution=dict(type='bool', required=False, default=False),
        no_prompt=dict(type='bool', required=False),
        force=dict(type='bool', required=False),
        ignore_errors=dict(type='bool', required=False, default=False),
        os_env=dict(type='str', required=False),
        syntax_11g=dict(type='bool', required=False,default=False),
        detail=dict(type='bool', required=False,default=False),
    )

    result = dict(
        changed=False,
        srvctl_message='',
        srvctl_command='',
        srvctl_output='',
        srvctl_os_env=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_srvctl = execute_srvctl(
        module.params['oracle_home'],
        module.params['add_oh_to_command'],
        module.params['oracle_unqname'],
        module.params['oracle_database'],
        module.params['oracle_instance'],
        module.params['oracle_node'],
        module.params['srvctl_command'],
        module.params['no_execution'],
        module.params['no_prompt'],
        module.params['force'],
        module.params['ignore_errors'],
        module.params['os_env'],
        module.params['syntax_11g'],
        module.params['detail']
        )
    
    result['srvctl_message'] = results_of_execute_srvctl[1]
    result['srvctl_output'] = results_of_execute_srvctl[0]
    result['srvctl_command'] = results_of_execute_srvctl[3]
    result['srvctl_os_env'] = results_of_execute_srvctl[4]


    if results_of_execute_srvctl[1] != '':
        module.fail_json(msg='SRVCTL module has failed (PRKO/PRCD/PRCT-XXXX errors listed)!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
