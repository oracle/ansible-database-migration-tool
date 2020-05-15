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
module: oracle_impdp_module

short_description: This is simple Oracle DataPump IMPDP module for remote execution

version_added: "1.0"

description:
    - "This module will help to execute Oracle DataPump IMPDP"

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
        required: false
    no_log_file:
        description:
            - no log file
        required: false
    transport_datafiles:
        description:
            - transportable datafiles that need to be imported.
        required: false   
    full:
        description:
            - full parameter of IMPDP
        required: false 
    encryption_password:
        description:
            - ENCRYPTION_PASSWORD parameter of IMPDP
        required: false 
    logfile:
        description:
            - logfile parameter of IMPDP
        required: false 
    schemas:
        description:
            - schemas parameter of IMPDP
        required: false


'''

EXAMPLES = '''
# Execute IMPDP remotely
- name: Import data via IMPDP
  oracle_impdp_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    directory: 'dmpdir'
    dumpfile: 'scott.dmp'

'''

RETURN = '''
impdp_message:
    description: result of impdp execution.
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

def execute_impdp(oracle_home, oracle_sid, directory, dumpfile, output_as_array, ignore_ORA_errors, username, password, as_sysdba, pdb_service, no_execution, no_log_file, transport_datafiles, full, encryption_password, logfile, schemas):

    if oracle_home is None:
       oracle_home = find_oracle_home(oracle_sid)

    args = [os.path.join(oracle_home, 'bin', 'impdp')]
    
    if username is not None and password is not None:
        if pdb_service is None:
            if as_sysdba is True:
                args.append('\''+username+"/"+password+' as sysdba\'')
            else:
                args.append(username+"/"+password)
        else:
            if as_sysdba is True: 
                args.append('\''+username+"/"+password+"@"+pdb_service+' as sysdba\'') 
            else:     
                args.append(username+"/"+password+"@"+pdb_service)    
    else:        
        args.append('\'/ as sysdba\'')

    args.append('directory='+directory)  
    args.append('dumpfile='+dumpfile)

    if transport_datafiles is not None:
        args.append('transport_datafiles='+transport_datafiles)

    if schemas is not None:
        args.append('schemas='+schemas)
    
    if no_log_file is not None:
        if no_log_file is True:
            args.append('nologfile=y')    
        else:
            args.append('nologfile=n')
    
    if full is not None:
        if full is True:
            args.append('full=y')    
        else:
            args.append('full=n')

    if encryption_password is not None:
        args.append('ENCRYPTION_PASSWORD='+encryption_password)        

    if logfile is not None:
        args.append('logfile='+logfile)     

    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    if no_execution is True:
        return [' '.join(args),'','']
    else:    
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
       
        impdpResult, stderrResult = p.communicate()

        #if impdpResult.count('ORA-') > 0:
        #
        #    if ignore_ORA_errors == False:            
        #        oraErrors = re.findall('ORA-(.+?):', impdpResult) 
        #    if ignore_ORA_errors == True:            
        #        oraErrors = ''          
        
        #if impdpResult.count('ORA-') == 0:
        #    oraErrors = ''

        #if impdpResult.count('LRM-') > 0:
        #
        #    if ignore_ORA_errors == False:            
        #        oraErrors = re.findall('LRM-(.+?):', impdpResult) 
        #    if ignore_ORA_errors == True:            
        #        oraErrors = ''          
        
        #if impdpResult.count('LRM-') == 0:
        #    oraErrors = ''    

        if stderrResult.count('ORA-') > 0:
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', stderrResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        if stderrResult.count('ORA-') == 0:
            #oraErrors = 'ORA-99999'
            oraErrors = ''

        if stderrResult.count('LRM-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('LRM-(.+?):', stderrResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if stderrResult.count('LRM-') == 0:
            oraErrors = ''        
    
        if output_as_array == True:
            impdpResult = impdpResult.split('\n')
            stderrResult = stderrResult.split('\n')
            impdpResult[:] = [item for item in impdpResult if item != '']


        return [impdpResult,oraErrors,stderrResult,' '.join(args)]

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
        transport_datafiles=dict(type='str', required=False),
        full=dict(type='bool', required=False),
        encryption_password=dict(type='str', required=False),
        logfile=dict(type='str', required=False),
        schemas=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
        impdp_output='',
        impdp_command=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_impdp = execute_impdp(
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
        module.params['transport_datafiles'],
        module.params['full'],
        module.params['encryption_password'],
        module.params['logfile'],
        module.params['schemas']
        )
    
    result['impdp_output'] = results_of_execute_impdp
    result['impdp_command'] = results_of_execute_impdp[3]

    if results_of_execute_impdp[2] != '':
        module.fail_json(msg='DataPump IMPDP module has failed (ORA/LRM-XXXX errors listed)!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
