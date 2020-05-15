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
module: oracle_sqlplus_module

short_description: This is simple SQLPLUS module for remote execution

version_added: "1.0"

description:
    - "This module will help to pickup some answers from SQLPLUS exectution"

options:
    oracle_home:
        description:
            - This is $ORACLE_HOME directory where RMAN binary resides (lack of parameter means it will be derived from /etc/oratab).
        required: false
    oracle_sid:
        description:
            - This is $ORACLE_SID which will be used to access proper database
        required: true
    oracle_unqname:
        description:
            - This is $ORACLE_UNQNAME which will be used to access proper database
        required: false    
    sql_statement:
        description:
            - This is SQL statement which will be executed
        required: true
    silent_mode:
        description:
            - SQLPLUS will be executed in silent mode.
        required: false
    spool_file:
        description:
            - SQLPLUS will be executed in with spool file.
        required: false        
    output_as_array:
        description:
            - Output of SQLPLUS will be delivered as one string (False) or as an array (True) line by line
        required: false
    output_set_heading_off:
        description:
            - Within SQLPLUS set heading off command will be executed 
        required: false
    output_set_feedback_off:
        description:
            - Within SQLPLUS set feedback off command will be executed 
        required: false
    ignore_ORA_errors:
        description:
            - When set to True module will ignore ORA-XXXX errors 
        required: false
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
    no_execution:
        description:
            - Show show the command which will be executed.
        required: false
    set_container:
        description:
            - will execute "alter session set container = <pdb_service>;" before sql_statement.
        required: false 
    restricted_session:
        description:
            - will execute "ALTER SYSTEM ENABLE RESTRICTED SESSION;" before sql_statement.                          
        required: false    
    tns_admin:
        description:
            - This is $TNS_ADMIN which will be used to access proper database
        required: false

'''

EXAMPLES = '''
# Execute SQLPlus remotely
- name: Check open mode of database
  oracle_sqlplus_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    sql_statement: 'select open_mode from v$database;'

# Execute SQLPlus remotely (output as array, oracle_home derived from /etc/oratab)
- name: Check open mode of database
  oracle_sqlplus_module:
    oracle_sid: '<SID>'
    sql_statement: 'select username from dba_users;'
    output_as_array: True
'''

RETURN = '''
sqlplus_message:
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

def execute_sqlplus(oracle_home, oracle_sid, oracle_unqname, sql_statement, silent_mode, spool_file, output_as_array, output_set_heading_off, output_set_feedback_off, ignore_ORA_errors, username, password, as_sysdba, pdb_service, no_execution, set_container, restricted_session, hidden_oracle_script, tns_admin):

    if oracle_home is None:
       oracle_home = find_oracle_home(oracle_sid)

    args = [os.path.join(oracle_home, 'bin', 'sqlplus')]
    
    if silent_mode == True: 
        args.append('-S')
    
    if username is not None and password is not None:
        if pdb_service is None:
            args.append(username+"/"+password)
        else:
            args.append(username+"/"+password+"@"+pdb_service)     
    else:
        args.append('/')    
        
    if as_sysdba is True:    
        args.append(' as sysdba')
    
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    if tns_admin is not None:
        my_env["TNS_ADMIN"] = tns_admin

    if oracle_unqname is not None:
        my_env["ORACLE_UNQNAME"] = oracle_unqname
    else:    
        my_env["ORACLE_UNQNAME"] = oracle_sid

    #if oracle_unqname in not None:
    #    my_env["ORACLE_UNQNAME"] = oracle_unqname
    #else:
    #    my_env["my_env["ORACLE_UNQNAME"] =     

    if no_execution is True:
        return ['','','',' '.join(args)]
    else:    
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)   

        if set_container == True:
            p.stdin.write(b' ALTER SESSION SET CONTAINER = '+pdb_service+';\n')

        if hidden_oracle_script == True:
            p.stdin.write(b' alter session set "_oracle_script"=TRUE;\n')    
 
        if restricted_session == True:
            p.stdin.write(b' ALTER SYSTEM ENABLE RESTRICTED SESSION;\n')

        if output_set_heading_off == True:
            p.stdin.write(b' SET HEADING OFF\n')

        if output_set_feedback_off == True:
            p.stdin.write(b' SET FEEDBACK OFF;\n')

        p.stdin.write(b' SET PAGES 999;\n')  
        p.stdin.write(b' SET LINESIZE 1000;\n')  
        p.stdin.write(b' SET TAB OFF;\n')  
    
        if spool_file is not None:
            p.stdin.write(b' SPOOL '+spool_file+'\n')

        p.stdin.write(sql_statement.encode())

        if spool_file is not None:
            p.stdin.write(b' SPOOL OFF\n')
    
        queryResult, stderrResult = p.communicate()

        if queryResult.count('ORA-') > 0:
        
            if ignore_ORA_errors == False:            
                oraErrors = re.findall('ORA-(.+?):', queryResult) 
            if ignore_ORA_errors == True:            
                oraErrors = ''          
        
        if queryResult.count('ORA-') == 0:
            oraErrors = ''
    
        if output_as_array == True:
            queryResult = queryResult.split('\n')
            queryResult[:] = [item for item in queryResult if item != '']

        return [queryResult,oraErrors,stderrResult,' '.join(args)]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        oracle_sid=dict(type='str', required=True),
        oracle_unqname=dict(type='str', required=False),
        sql_statement=dict(type='str', required=True),
        silent_mode=dict(type='bool', required=False, default=True),
        spool_file=dict(type='str', required=False),
        output_as_array=dict(type='bool', required=False, default=True),
        output_set_heading_off=dict(type='bool', required=False, default=True),
        output_set_feedback_off=dict(type='bool', required=False, default=True),
        ignore_ORA_errors=dict(type='bool', required=False, default=False),
        username=dict(type='str', required=False),    
        password=dict(type='str', required=False),
        as_sysdba=dict(type='bool', required=False, default=True),  
        pdb_service=dict(type='str', required=False),
        no_execution=dict(type='bool', required=False, default=False), 
        set_container=dict(type='bool', required=False, default=False),
        restricted_session=dict(type='bool', required=False, default=False),
        hidden_oracle_script=dict(type='bool', required=False, default=False),
        tns_admin=dict(type='str', required=False, default=False) 
    )

    result = dict(
        changed=False,
        sqlplus_message='',
        sqlplus_command=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_sqlplus = execute_sqlplus(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['oracle_unqname'],
        module.params['sql_statement'],
        module.params['silent_mode'],
        module.params['spool_file'],
        module.params['output_as_array'],
        module.params['output_set_heading_off'],
        module.params['output_set_feedback_off'],
        module.params['ignore_ORA_errors'],
        module.params['username'],
        module.params['password'],
        module.params['as_sysdba'],
        module.params['pdb_service'],
        module.params['no_execution'],
        module.params['set_container'],
        module.params['restricted_session'],
        module.params['hidden_oracle_script'],
        module.params['tns_admin'])

    
    result['sqlplus_message'] = results_of_execute_sqlplus
    result['sqlplus_command'] = results_of_execute_sqlplus[3]
 
    #module.log(msg=str(result['sqlplus_message']))

    if results_of_execute_sqlplus[1] != '':
        module.fail_json(msg='SQLPLUS module has failed (ORA-XXXX errors listed)!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
