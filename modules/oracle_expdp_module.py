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
module: oracle_expdp_module

short_description: This is simple Oracle DataPump EXPDP module for remote execution

version_added: "1.0"

description:
    - "This module will help to execute Oracle DataPump EXPDP"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where RMAN binary resides (lack of parameter means it will be derived from /etc/oratab).
        required: false
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database
        required: true
    username:
        description:
            - database username which should be used for login to database 
        required: false
    password:
        description:
            - database user's password which should be used for login to database 
        required: false
    as_sysdba:
        description:
            - database user's can be logged as sysdba 
        required: false
    pdb_service:    
        description:
            - database user's can be logged to particular PDB
        required: false
    ignore_ORA_errors:
        description:
            - When set to True module will ignore ORA-XXXX errors 
        required: false    
    directory:
        description:
            - the name of DIRECTORY object
        required: true
    dumpfile:
        description:
            - the path and file of dumpfile.
        required: true                    
    no_execution:
        description:
            - Show show the command which will be executed.
        required: false
    output_as_array:
        description:
            - Output of RMAN will be delivered as one string (False) or as an array (True) line by line
    no_log_file:
        description:
            - no log file
        required: false
    transportable:
        description:
            - transportable parameter of EXPDP
        required: false   
    version:
        description:
            - version parameter of EXPDP
        required: false  
    full:
        description:
            - full parameter of EXPDP
        required: false  
    encryption_password:
        description:
            - ENCRYPTION_PASSWORD parameter of EXPDP
        required: false
    transport_full_check:
        description:
            - TRANSPORT_FULL_CHECK parameter of EXPDP
        required: false
    transport_tablespaces:
        description:
            - TRANSPORT_TABLESPACES parameter of EXPDP
        required: false
    schemas:
        description:
            - SCHEMAS parameter of EXPDP
        required: false    



'''

EXAMPLES = '''
# Execute EXPDP remotely
- name: Export data via EXPDP
  oracle_expdp_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    directory: 'dmpdir'
    dumpfile: 'scott.dmp'

'''

RETURN = '''
expdp_message:
    description: result of expdp execution.
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

def execute_expdp(oracle_home, oracle_sid, directory, dumpfile, output_as_array, ignore_ORA_errors, username, password, as_sysdba, pdb_service, no_execution, no_log_file, transportable, version, full, encryption_password, transport_full_check, transport_tablespaces, schemas):

    if oracle_home is None:
       oracle_home = find_oracle_home(oracle_sid)

    args = [os.path.join(oracle_home, 'bin', 'expdp')]
    
    if username is not None and password is not None:
        if pdb_service is None:
            args.append(username+"/"+password)
        else:
            args.append(username+"/"+password+"@"+pdb_service)    
        
    if as_sysdba is True:    
        args.append('\"/ as sysdba\"')

    args.append('directory='+directory)  
    args.append('dumpfile='+dumpfile)

    if transportable is not None:
        args.append('transportable='+transportable)

    if transport_tablespaces is not None:
        args.append('transport_tablespaces='+transport_tablespaces)    
    
    if version is not None:
        args.append('version='+version)

    if full is not None:
        if full is True:
            args.append('full=y')    
        else:
            args.append('full=n')

    if encryption_password is not None:
        args.append('ENCRYPTION_PASSWORD='+encryption_password) 
    
    if schemas is not None:
        args.append('SCHEMAS='+schemas)  

    if transport_full_check is not None:
        if transport_full_check is True:
            args.append('TRANSPORT_FULL_CHECK=y')
        else:
            args.append('TRANSPORT_FULL_CHECK=n')             

    if no_log_file is not None:        
        if no_log_file is True:
            args.append('nologfile=y')    
        else:
            args.append('nologfile=n')
    
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    if no_execution is True:
        return [' '.join(args),'','']
    else:    
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
       
        expdpResult, stderrResult = p.communicate()

        if expdpResult.count('ORA-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', expdpResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if expdpResult.count('ORA-') == 0:
            oraErrors = ''

        if expdpResult.count('LRM-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('LRM-(.+?):', expdpResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if expdpResult.count('LRM-') == 0:
            oraErrors = ''    

        if stderrResult.count('ORA-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', stderrResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if stderrResult.count('ORA-') == 0:
            oraErrors = ''

        if stderrResult.count('LRM-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('LRM-(.+?):', stderrResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if stderrResult.count('LRM-') == 0:
            oraErrors = ''        
    
        if output_as_array == True:
            expdpResult = expdpResult.split('\n')
            stderrResult = stderrResult.split('\n')
            expdpResult[:] = [item for item in expdpResult if item != '']

        return [expdpResult,oraErrors,stderrResult]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False), 
        oracle_sid=dict(type='str', required=True), 
        directory=dict(type='str', required=True), 
        dumpfile=dict(type='str', required=True), 
        output_as_array=dict(type='bool', required=False, default=True), 
        ignore_ORA_errors=dict(type='bool', required=False, default=False), 
        username=dict(type='str', required=False),    
        password=dict(type='str', required=False),
        as_sysdba=dict(type='bool', required=False, default=False),  
        pdb_service=dict(type='str', required=False),
        no_execution=dict(type='bool', required=False, default=False),
        no_log_file=dict(type='bool', required=False), 
        transportable=dict(type='str', required=False),
        version=dict(type='str', required=False),
        full=dict(type='bool', required=False),
        encryption_password=dict(type='str', required=False),
        transport_full_check=dict(type='bool', required=False),
        transport_tablespaces=dict(type='str', required=False),
        schemas=dict(type='str', required=False)   
    )

    result = dict(
        changed=False,
        expdp_message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_expdp = execute_expdp(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['directory'],
        module.params['dumpfile'],
        module.params['output_as_array'],
        module.params['ignore_ORA_errors'],
        module.params['username'],
        module.params['password'],
        module.params['as_sysdba'],
        module.params['pdb_service'],
        module.params['no_execution'],
        module.params['no_log_file'],
        module.params['transportable'],
        module.params['version'],
        module.params['full'],
        module.params['encryption_password'],
        module.params['transport_full_check'],
        module.params['transport_tablespaces'],
        module.params['schemas']
        )
    
    result['expdp_message'] = results_of_execute_expdp

    if results_of_execute_expdp[1] != '':
        module.fail_json(msg='DataPump EXPDP module has failed (ORA/LRM-XXXX errors listed)!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
