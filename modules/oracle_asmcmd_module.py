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
module: oracle_asmcmd_module

short_description: This is simple Oracle ASMCMD module for remote execution

version_added: "1.0"

description:
    - "This module will help to execute Oracle ASMCMD utility"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where ASMCMD binary resides 
        required: true
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database (if not provided +ASM1 will be chosen)
        required: false
    asmcmd_script:
        description:
            - This will be executed within ASMCMD
        required: true
    no_execution:
        description:
            - Show show the command which will be executed.
        required: false
    output_as_array:
        description:
            - Output of RMAN will be delivered as one string (False) or as an array (True) line by line
        required: false
    ignore_ORA_errors:
        description:
            - When set to True module will ignore ORA-XXXX errors 
        required: false    
    
'''

EXAMPLES = '''
# Execute ASMCMD 
- name: copy vdb.ctf1 control file from ASM to filesystem.
  oracle_asmcmd_module:
    oracle_home: '/u01/app/12.2.0.1/grid'
    oracle_sid: '+ASM1'
    asmcmd_script: 'cp +DG1/vdb.ctf1 /backups/vdb.ctf1'
    
'''

RETURN = '''
asmcmd_message:
    description: result of SQL statement.
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

def execute_asmcmd(oracle_home, oracle_sid, output_as_array, no_execution, ignore_ORA_errors, asmcmd_script):

    args = [os.path.join(oracle_home, 'bin', 'asmcmd')]
    
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    if no_execution is True:
        return [' '.join(args),'','']
    else:    
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)  
        p.stdin.write(asmcmd_script.encode())  
       
        asmcmdResult, stderrResult = p.communicate()

        if asmcmdResult.count('ORA-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', asmcmdResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if asmcmdResult.count('ORA-') == 0:
            oraErrors = ''

        if stderrResult.count('ORA-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', stderrResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if stderrResult.count('ORA-') == 0:
            oraErrors = ''

        if output_as_array == True:
            asmcmdResult = asmcmdResult.split('\n')
            asmcmdResult[:] = [item for item in asmcmdResult if item != '']

        return [asmcmdResult,oraErrors,stderrResult]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=True), 
        oracle_sid=dict(type='str', required=False), 
        no_execution=dict(type='bool', required=False, default=False),
        output_as_array=dict(type='bool', required=False, default=True), 
        ignore_ORA_errors=dict(type='bool', required=False, default=False), 
        asmcmd_script=dict(type='str', required=True)
        
    )

    result = dict(
        changed=False,
        asmcmd_message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_asmcmd = execute_asmcmd(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['output_as_array'],
        module.params['no_execution'],
        module.params['ignore_ORA_errors'],
        module.params['asmcmd_script'])

    result['asmcmd_message'] = results_of_execute_asmcmd

    if results_of_execute_asmcmd[1] != '':
        module.fail_json(msg='ASMCMD module has failed (ORA-XXXX errors listed)!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
