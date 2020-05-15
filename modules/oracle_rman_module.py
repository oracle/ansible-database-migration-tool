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
module: oracle_rman_module

short_description: This is simple RMAN (Oracle Recovery Manager) module for remote execution

version_added: "1.0"

description:
    - "This module will execute RMAN script over particular database"

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
    rman_script:
        description:
            - This is RMAN script which will be executed
        required: true
    rman_connect_target_string:
        description:
            - You can define connect target string (user, password, PDB etc). If not set target=/ will be used.
        required: false
    rman_logfile:
        description:
            - This is RMAN script which will be executed
        required: false
    output_as_array:
        description:
            - Output of RMAN will be delivered as one string (False) or as an array (True) line by line
        required: false 
    output_omit_heading:
        description:
            - Output of RMAN will be delivered as array and first 6 lines (heading) will be omitted
        required: false
    output_omit_ending:
            description:
            - Output of RMAN will be delivered as array and last 5 lines (ending) will be omitted
        required: false
    output_omit_all:
            description:
            - Output of RMAN will not be delivered 
        required: false
    ignore_RMAN_errors:
        description:
            - When set to True module will ignore RMAN-XXXX errors 
        required: false 
    output_backupsets
            description:
            - Delivers backupset names list
        required: false
    output_backupsets_only_filenames
            description:
            - Delivers backupset names list without path (only filenames)
        required: false
    output_datafile_file_numbers
        description:
            - Delivers input datafile list of numbers which will be included in backupsets. 
        required: false
    output_datafile_file_names
        description:
            - Delivers input datafile list of filenames which will be included in backupsets. 
        required: false
    debug_trace:
        description:
            - Enables debug trace for RMAN session. You provide the name of debug_trace path+filename. 
        required: false
        
                           
           
'''

EXAMPLES = '''
# Backup database with RMAN (output RMAN as string, RMAN heading included)
- name: Backup database
  oracle_rman_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    rman_script: 'backup database;'

# Backup database with RMAN (oracle_home derived automatically from /etc/oratab,
# output RMAN as array, RMAN heading & ending included)
- name: Backup database
  oracle_rman_module:
    oracle_sid: '<SID>'
    rman_script: 'backup database;'
    rman_logfile: '/tmp/rman_backup_database.log'
    output_as_array: True


# List RMAN backups (output as array, omit RMAN heading and ending) 
- name: List backups
  oracle_rman_module:
    oracle_home: '/u01/app/oracle/product/12.1.0.2/dbhome_1'
    oracle_sid: '<SID>'
    rman_script: 'list backup;'
    output_as_array: True
    output_omit_heading: True
    output_omit_ending: True    

'''

RETURN = '''
rman_output:
    description: result of RMAN execution.
    type: str
changed:
    description: will be used for the future all removed.
    type: bool   
'''

from ansible.module_utils.basic import AnsibleModule
from subprocess import Popen, PIPE
from tempfile import mkstemp, TemporaryFile
from datetime import datetime, timedelta
import os, sys, re, mmap

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

def find_output_backupsets(rmanoutput,output_backupsets_only_filenames):
   
    output_backupsets = []
    re_output_backupsets = re.compile(r'piece handle=(?P<BACKUPSET_FILENAME>(/|\w+|\.|\d|\+)+) ')
    try:
        for m in re_output_backupsets.finditer(rmanoutput):
            head, tail = os.path.split(m.group('BACKUPSET_FILENAME'))
            if output_backupsets_only_filenames is True:
                output_backupsets.append(tail)
            else:    
                output_backupsets.append(head+'/'+tail)
    except Exception: 
        output_backupsets = []
    
    return output_backupsets               

def find_output_datafile_file_numbers(rmanoutput):
   
    output_datafile_file_numbers = []
    re_output_datafile_file_numbers = re.compile(r'input datafile file number=(?P<FILE_NUMBER>(/|\w+|\.|\d)+) name')
    try:
        for m in re_output_datafile_file_numbers.finditer(rmanoutput):
            output_datafile_file_numbers.append(m.group('FILE_NUMBER').lstrip("0"))
    except Exception: 
        output_datafile_file_numbers = []
    
    return output_datafile_file_numbers    

def find_output_datafile_file_names(rmanoutput):
   
    output_datafile_file_names = []
    re_output_datafile_file_names = re.compile(r'input datafile file number=(?P<FILE_NUMBER>(/|\w+|\.|\d)+) name=(?P<FILE_NAME>(/|\w+|\.|\d|\+)+)')
    try:
        for m in re_output_datafile_file_names.finditer(rmanoutput):
            output_datafile_file_names.append(m.group('FILE_NAME'))
    except Exception: 
        output_datafile_file_names = []
    
    return output_datafile_file_names  

def find_output_config_channel_sbt_tape_parms_sbt_library_dir(rmanoutput,oracle_home):
   
    output_config_channel_sbt_tape_parms_sbt_library_dir = []
    re_output_config_channel_sbt_tape_parms_sbt_library_dir = re.compile(r'SBT_LIBRARY=(?P<SBT_LIBRARY>(/|\w+|\.|\d|\+)+)libopc')
    try:
        for m in re_output_config_channel_sbt_tape_parms_sbt_library_dir.finditer(rmanoutput):
            output_config_channel_sbt_tape_parms_sbt_library_dir.append(m.group('SBT_LIBRARY'))
        if not output_config_channel_sbt_tape_parms_sbt_library_dir:
            output_config_channel_sbt_tape_parms_sbt_library_dir.append(oracle_home+'/lib')
    except Exception: 
        output_config_channel_sbt_tape_parms_sbt_library_dir = []
    
    return output_config_channel_sbt_tape_parms_sbt_library_dir            

def find_output_config_channel_sbt_tape_parms_sbt_opc_pfile(rmanoutput):
   
    output_config_channel_sbt_tape_parms_sbt_opc_pfile = []
    re_output_config_channel_sbt_tape_parms_sbt_opc_pfile = re.compile(r'OPC_PFILE=(?P<OPC_PFILE>(/|\w+|\.|\d|\+)+)\)')
    try:
        for m in re_output_config_channel_sbt_tape_parms_sbt_opc_pfile.finditer(rmanoutput):
            output_config_channel_sbt_tape_parms_sbt_opc_pfile.append(m.group('OPC_PFILE'))
    except Exception: 
        output_config_channel_sbt_tape_parms_sbt_opc_pfile = []
    
    return output_config_channel_sbt_tape_parms_sbt_opc_pfile         


def execute_rman(oracle_home, oracle_sid, oracle_unqname, rman_script, rman_connect_target_string, rman_logfile, output_as_array, output_omit_heading, output_omit_ending, output_omit_all, ignore_RMAN_errors, output_datafile_file_numbers, output_datafile_file_names, output_backupsets, output_backupsets_only_filenames, output_config_channel_sbt_tape_parms_sbt_library_dir, output_config_channel_sbt_tape_parms_sbt_opc_pfile, debug_trace):


    if oracle_home is None:
       oracle_home = find_oracle_home(oracle_sid)

    args = [os.path.join(oracle_home, 'bin', 'rman')]
    if rman_connect_target_string is not None:
       args.append(" target=\"'"+rman_connect_target_string+"'\"")   
    else:    
        args.append(' target=/')

#    if rman_logfile is not None:
#        args.append(' log = '+rman_logfile+' APPEND')
    
    if debug_trace is not None:
        args.append(' debug trace='+debug_trace)

    #if rman_logfile is not None:
    #    args.append(' | tee '+rman_logfile)
    
    my_env = os.environ.copy()
    my_env["PATH"] = my_env["PATH"] + oracle_home+'/bin'
    my_env["ORACLE_HOME"] = oracle_home
    my_env["ORACLE_SID"] = oracle_sid

    if oracle_unqname is not None:
        my_env["ORACLE_UNQNAME"] = oracle_unqname
    else:
        my_env["ORACLE_UNQNAME"] = oracle_sid
    
    
    if rman_logfile is not None:
        outfile=open(rman_logfile,"wb")
        errfile=open(rman_logfile,"wb")
        p = Popen(args, stdout=outfile, stderr=errfile, env=my_env, stdin=PIPE)    
        p.stdin.write(rman_script.encode())
        rmanResult, stderrResult = p.communicate()
        outfile=open(rman_logfile,"r")
        errfile=open(rman_logfile,"r")
        rmanResult=outfile.read() 
        stderrResult=errfile.read() 
    else:            
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE) 
        p.stdin.write(rman_script.encode())
        rmanResult, stderrResult = p.communicate() 

    #p.stdin.write(rman_script.encode())

    #rmanResult, stderrResult = p.communicate()


    if rmanResult.count('RMAN-') > 0:
        if ignore_RMAN_errors == False: 
            rmanErrors = re.findall('RMAN-(.+?):', rmanResult)
        if ignore_RMAN_errors == True:
            rmanErrors = ''        
        
    if rmanResult.count('RMAN-') == 0:
        rmanErrors = ''

    
    if output_datafile_file_numbers is True:    
        datafileNumbers = find_output_datafile_file_numbers(rmanResult)
    else:
        datafileNumbers = []

    if output_datafile_file_names is True:    
        datafileNames = find_output_datafile_file_names(rmanResult)
    else:
        datafileNames = []          

    if output_backupsets is True:    
        backupsets = find_output_backupsets(rmanResult, output_backupsets_only_filenames)
    else:
        backupsets = []       

    if output_config_channel_sbt_tape_parms_sbt_library_dir is True:    
        config_channel_sbt_tape_parms_sbt_library_dir = find_output_config_channel_sbt_tape_parms_sbt_library_dir(rmanResult, oracle_home)
    else:
        config_channel_sbt_tape_parms_sbt_library_dir = []     

    if output_config_channel_sbt_tape_parms_sbt_opc_pfile is True:    
        config_channel_sbt_tape_parms_sbt_opc_pfile = find_output_config_channel_sbt_tape_parms_sbt_opc_pfile(rmanResult)
    else:
        config_channel_sbt_tape_parms_sbt_opc_pfile = []   

    if output_as_array == True:
        rmanResult = rmanResult.split('\n')
        if output_omit_heading == True:
            rmanResult = rmanResult[6:]
        if output_omit_ending == True:
            rmanResult = rmanResult[:len(rmanResult)-5]
    
    if output_omit_all == True:
        rmanResult = ''

    return [rmanResult, rmanErrors, stderrResult, backupsets, datafileNumbers, datafileNames, config_channel_sbt_tape_parms_sbt_library_dir, config_channel_sbt_tape_parms_sbt_opc_pfile]

def run_module():
    
    module_args = dict(
        oracle_home=dict(type='str', required=False),
        oracle_sid=dict(type='str', required=True),
        oracle_unqname=dict(type='str', required=False),
        rman_script=dict(type='str', required=True),
        rman_connect_target_string=dict(type='str', required=False),
        rman_logfile=dict(type='str', required=False),
        output_as_array=dict(type='bool', required=False, default=True),
        output_omit_heading=dict(type='bool', required=False, default=True),
        output_omit_ending=dict(type='bool', required=False, default=True),
        output_omit_all=dict(type='bool', required=False, default=False), 
        ignore_RMAN_errors=dict(type='bool', required=False, default=False), 
        output_backupsets=dict(type='bool', required=False, default=True),
        output_datafile_file_numbers=dict(type='bool', required=False, default=True),
        output_datafile_file_names=dict(type='bool', required=False, default=True),
        output_backupsets_only_filenames=dict(type='bool', required=False, default=True),
        output_config_channel_sbt_tape_parms_sbt_library_dir=dict(type='bool', required=False, default=False),
        output_config_channel_sbt_tape_parms_sbt_opc_pfile=dict(type='bool', required=False, default=False),
        debug_trace=dict(type='str', required=False)
        
    )

    result = dict(
        changed=False,
        rman_output='',
        backupsets='',
        datafile_file_numbers='',
        datafile_file_names='',
        config_channel_sbt_tape_parms_sbt_library_dir='',
        config_channel_sbt_tape_parms_sbt_opc_pfile='',

    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

      
    results_of_execute_rman = execute_rman(
        module.params['oracle_home'],
        module.params['oracle_sid'],
        module.params['oracle_unqname'],
        module.params['rman_script'], 
        module.params['rman_connect_target_string'], 
        module.params['rman_logfile'],
        module.params['output_as_array'],
        module.params['output_omit_heading'],
        module.params['output_omit_ending'],
        module.params['output_omit_all'],
        module.params['ignore_RMAN_errors'],
        module.params['output_datafile_file_numbers'], 
        module.params['output_datafile_file_names'], 
        module.params['output_backupsets'], 
        module.params['output_backupsets_only_filenames'],
        module.params['output_config_channel_sbt_tape_parms_sbt_library_dir'],
        module.params['output_config_channel_sbt_tape_parms_sbt_opc_pfile'],
        module.params['debug_trace'])
    
    result['rman_output'] = results_of_execute_rman[0]
    result['backupsets'] = results_of_execute_rman[3]
    result['datafile_file_numbers'] = results_of_execute_rman[4]
    result['datafile_file_names'] = results_of_execute_rman[5]
    result['config_channel_sbt_tape_parms_sbt_library_dir'] = results_of_execute_rman[6]
    result['config_channel_sbt_tape_parms_sbt_opc_pfile'] = results_of_execute_rman[7]

            
    if results_of_execute_rman[1] != '':
        module.fail_json(msg='RMAN module has failed (RMAN-XXXX errors listed)!', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
