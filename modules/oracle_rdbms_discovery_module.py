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
module: oracle_rdbms_discovery_module

short_description: This module discover oracle RDBMS database 

version_added: "1.0"

description:
    - "This module discover oracle RDBMS database"

options:

'''

EXAMPLES = '''
# Execute discovery with all parameters
- name: Check open mode of database
  oracle_rdbms_discovery_module:
    
'''

RETURN = '''
oracle_home:
    description: ORACLE_HOME for delivered ORACLE_dbname on start (according to oratab file)
    type: str
oracle_gi_home:
    description: Oracle Grid Infrastructure Home
    type: str
crs_enabled:
    description: Check if Grid Infrastructure is enabled in this configuration.
    type: Bool 
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
                
def find_ora_inv_loc():

    re_ora_inventory = re.compile(r'^inventory_loc=(?P<ORA_INV_LOC>(/|\w+|\.)+)')

    with open('/etc/oraInst.loc', 'r') as f:
        for line in f:
            line = line.strip()
            re_ora_inventory_match = re_ora_inventory.search(line)
            if re_ora_inventory_match:
                try:
                    ora_inventory = re_ora_inventory_match.group('ORA_INV_LOC')
                except Exception: 
                    ora_inventory = ''
                return ora_inventory

def find_ora_inv_oradb_home(inventory_loc):

    if inventory_loc is None:
        inventory_loc = '/u01/app/oraInventory/'

    re_oradb_home = re.compile(r'^<HOME NAME=\"OraD(?P<OHOME_NAME>(/|\w+|\.)+)\" LOC=\"(?P<OHOME_LOC>(/|\w+|\.)+)\" TYPE=\"O\" IDX=\"(?P<OHOME_IDX>(/|\w+|\.)+)\"')

    with open(inventory_loc+'/ContentsXML/inventory.xml', 'r') as f:
        for line in f:
            line = line.strip()
            re_oradb_home_match = re_oradb_home.search(line)
            if re_oradb_home_match:
                try:
                    oradb_home = re_oradb_home_match.group('OHOME_LOC')
                except Exception: 
                    oradb_home = ''
                return oradb_home

def find_ora_inv_oradb_home_no_grid(inventory_loc):

    if inventory_loc is None:
        inventory_loc = '/u01/app/oraInventory/'

    re_oradb_home = re.compile(r'^<HOME NAME=\"(?P<OHOME_NAME>(/|\w+|\.)+)\" LOC=\"(?P<OHOME_LOC>(/|\w+|\.)+)\" TYPE=\"O\" IDX=\"(?P<OHOME_IDX>(/|\w+|\.)+)\"/>')

    with open(inventory_loc+'/ContentsXML/inventory.xml', 'r') as f:
        for line in f:
            line = line.strip()
            re_oradb_home_match = re_oradb_home.search(line)
            if re_oradb_home_match:
                try:
                    oradb_home = re_oradb_home_match.group('OHOME_LOC')
                except Exception: 
                    oradb_home = ''
                return oradb_home                

def find_ora_inv_grid_home(inventory_loc):

    if inventory_loc is None:
        inventory_loc = '/u01/app/oraInventory/'

    re_grid_home = re.compile(r'^<HOME NAME=\"OraG(?P<OHOME_NAME>(/|\w+|\.)+)\" LOC=\"(?P<OHOME_LOC>(/|\w+|\.)+)\" TYPE=\"O\" IDX=\"(?P<OHOME_IDX>(/|\w+|\.)+)\" CRS=\"(?P<CRS>(/|\w+|\.)+)\"')

    with open(inventory_loc+'/ContentsXML/inventory.xml', 'r') as f:
        for line in f:
            line = line.strip()
            re_grid_home_match = re_grid_home.search(line)
            if re_grid_home_match:
                try:
                    grid_home = re_grid_home_match.group('OHOME_LOC')
                except Exception: 
                    grid_home = ''
                return grid_home

def find_ora_inv_grid_crs(inventory_loc):

    if inventory_loc is None:
        inventory_loc = '/u01/app/oraInventory/'

    re_crs = re.compile(r'^<HOME NAME=\"OraG(?P<OHOME_NAME>(/|\w+|\.)+)\" LOC=\"(?P<OHOME_LOC>(/|\w+|\.)+)\" TYPE=\"O\" IDX=\"(?P<OHOME_IDX>(/|\w+|\.)+)\" CRS=\"(?P<CRS>(/|\w+|\.)+)\"')

    with open(inventory_loc+'/ContentsXML/inventory.xml', 'r') as f:
        for line in f:
            line = line.strip()
            re_crs_match = re_crs.search(line)
            if re_crs_match:
                try:
                    crs = re_crs_match.group('CRS')
                except Exception: 
                    crs = 'false'
                return crs.capitalize()   

def find_oracle_dbname_in_oratab(oracle_home):


    re_db_dbname = re.compile(r'^(?P<ORA_DBNAME>(/|\w+|\d)+):('+oracle_home+'):(Y|N)')

    with open('/etc/oratab', 'r') as f:
        for line in f:
            line = line.strip()
            re_db_dbname_match = re_db_dbname.search(line)
            if re_db_dbname_match:
                try:
                    db_dbname = re_db_dbname_match.group('ORA_DBNAME')
                except Exception: 
                    db_dbname = ""
                return db_dbname                             

def find_oracle_db_unique_name_in_crsctl(oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('-t')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_crsctl_db_unique_name = re.compile(r'ora\.(?P<DB_UNIQUE_NAME>(/|\w+|\.|\d|\-)+)\.db')
        re_crsctl_db_unique_name_match = re_crsctl_db_unique_name.search(stdoutResult)
        try:
            crsctl_db_unique_name = re_crsctl_db_unique_name_match.group('DB_UNIQUE_NAME')
        except Exception: 
            crsctl_db_unique_name = ''
        return crsctl_db_unique_name  

def find_oracle_home_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-f')     
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_ohome = re.compile(r'ORACLE_HOME=(?P<OHOME>(/|\w+|\.|\d|\-)+)')
        re_ohome_match = re_ohome.search(stdoutResult)
        try:
            ohome = re_ohome_match.group('OHOME')
        except Exception: 
            ohome = ''
        return ohome

def find_database_type_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-p')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_database_type = re.compile(r'DATABASE_TYPE=(?P<DATABASE_TYPE>(/|\w+|\.|\d|\-)+)')
        re_database_type_match = re_database_type.search(stdoutResult)
        try:
            database_type = re_database_type_match.group('DATABASE_TYPE')
        except Exception: 
            database_type = ''
        return database_type

def find_database_cardinality_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-p')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_database_cardinality = re.compile(r'CARDINALITY=(?P<DATABASE_CARDINALITY>(/|\w+|\.|\d|\-)+)')
        re_database_cardinality_match = re_database_cardinality.search(stdoutResult)
        try:
            database_cardinality = re_database_cardinality_match.group('DATABASE_CARDINALITY')
        except Exception: 
            database_cardinality = ''
        return database_cardinality

def find_dbname_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-p')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_database_name = re.compile(r'USR_ORA_DB_NAME=(?P<DATABASE_NAME>(/|\w+|\.|\d|\-)+)')
        re_database_name_match = re_database_name.search(stdoutResult)
        try:
            database_name = re_database_name_match.group('DATABASE_NAME')
        except Exception: 
            database_name = ''
        return database_name

def find_db_servers_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-p')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_db_servers = re.compile(r'GEN_USR_ORA_INST_NAME@SERVERNAME\((?P<HOSTNAME>(/|\w+|\.|\d|\-)+)\)');
        re_db_servers_match = re_db_servers.search(stdoutResult)
        count = 1
        outputtext = stdoutResult
        db_servers = []
        while re_db_servers_match:
            #print 'match %d: %s' % (count,re_db_servers_match.group('HOSTNAME'))
            db_servers.append(re_db_servers_match.group('HOSTNAME'))
            count = count + 1
            outputtext = outputtext[re_db_servers_match.end(1) + 1:]
            re_db_servers_match = re_db_servers.search(outputtext) 
        return db_servers

def find_db_instances_in_crsctl(oracle_dbname, oracle_gi_home):
    
    my_env = os.environ.copy()
    args = [os.path.join(oracle_gi_home, 'bin', 'crsctl')]
    args.append('stat')
    args.append('res')
    args.append('ora.'+oracle_dbname.lower()+'.db')
    args.append('-f')    
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    if stderrResult != '':
        return ''
    else: 
        re_db_instances = re.compile(r'GEN_USR_ORA_INST_NAME@SERVERNAME\((?P<HOSTNAME>(/|\w+|\.|\d|\-)+)\)=(?P<INSTANCE>(/|\w+|\.|\d|\-)+)');
        re_db_instances_match = re_db_instances.search(stdoutResult)
        count = 1
        outputtext = stdoutResult
        db_instances = []
        while re_db_instances_match:
            #print 'match %d: %s' % (count,re_db_instances_match.group('INSTANCE'))
            db_instances.append(re_db_instances_match.group('INSTANCE'))
            count = count + 1
            outputtext = outputtext[re_db_instances_match.end(1) + 1:]
            re_db_instances_match = re_db_instances.search(outputtext) 

        return db_instances

def execute_main(ora_inventory_location, etc_oratab_usage, oracle_dbname):

    database_type = None
    database_cardinality = None
    instances = None
    servers = None

    if oracle_dbname == '':
        oracle_dbname = None

    oracle_db_unique_name = oracle_dbname

    if ora_inventory_location is None:
        ora_inventory_location = find_ora_inv_loc()

    crs_enabled = find_ora_inv_grid_crs(ora_inventory_location)
    grid_home = find_ora_inv_grid_home(ora_inventory_location)

    if oracle_dbname is not None:
        if crs_enabled == 'True':
            oracle_home = find_oracle_home_in_crsctl(oracle_dbname, grid_home)
            database_type = find_database_type_in_crsctl(oracle_dbname, grid_home)
            database_cardinality = find_database_cardinality_in_crsctl(oracle_dbname, grid_home)
            instances = find_db_instances_in_crsctl(oracle_dbname, grid_home)
            servers = find_db_servers_in_crsctl(oracle_dbname, grid_home)
            oracle_dbname = find_dbname_in_crsctl(oracle_db_unique_name, grid_home)
        else:
            oracle_home = None
    else:
        oracle_home = None
    
    if oracle_home is None:
        oracle_home = find_ora_inv_oradb_home(ora_inventory_location)

    if oracle_home is None:
        oracle_home = find_ora_inv_oradb_home_no_grid(ora_inventory_location)

    if etc_oratab_usage:
        if oracle_dbname is None:
            if oracle_home is not None:
                oracle_dbname = find_oracle_dbname_in_oratab(oracle_home)
    
   # if oracle_dbname is None: 
    if crs_enabled == 'True':
            oracle_db_unique_name = find_oracle_db_unique_name_in_crsctl(grid_home)
            database_type = find_database_type_in_crsctl(oracle_db_unique_name, grid_home)
            database_cardinality = find_database_cardinality_in_crsctl(oracle_db_unique_name, grid_home)
            instances = find_db_instances_in_crsctl(oracle_db_unique_name, grid_home)
            servers = find_db_servers_in_crsctl(oracle_db_unique_name, grid_home)
            oracle_dbname = find_dbname_in_crsctl(oracle_db_unique_name, grid_home)
    
    if grid_home is None:
        grid_home = ''

    if crs_enabled is None:
        crs_enabled = 'False'

    return ['',oracle_home, oracle_dbname, oracle_db_unique_name, grid_home, crs_enabled, ora_inventory_location, database_type, database_cardinality, instances, servers]

def run_module():
    
    module_args = dict(
        ora_inventory_location=dict(type='str', required=False), 
        etc_oratab_usage=dict(type='bool', required=False, default=True),   
        oracle_dbname=dict(type='str', required=False),            
    )

    result = dict(
        changed=False,
        oracle_home='',
        oracle_dbname='',
        oracle_gi_home='',
        oracle_crs_enabled='',
        oracle_inventory_location='',
        oracle_database_type='',
        oracle_database_cardinality='',
        oracle_database_instances='',
        oracle_database_servers='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_main = execute_main(module.params['ora_inventory_location'], module.params['etc_oratab_usage'], module.params['oracle_dbname'])  
    result['oracle_home'] = results_of_execute_main[1]
    result['oracle_dbname'] = results_of_execute_main[2]
    result['oracle_db_unique_name'] = results_of_execute_main[3]
    result['oracle_gi_home'] = results_of_execute_main[4]
    result['oracle_crs_enabled'] = results_of_execute_main[5]
    result['oracle_inventory_location'] = results_of_execute_main[6]
    result['oracle_database_type'] = results_of_execute_main[7]
    result['oracle_database_cardinality'] = results_of_execute_main[8]
    result['oracle_database_instances'] = results_of_execute_main[9]
    result['oracle_database_servers'] = results_of_execute_main[10]

    if results_of_execute_main[0] != '':
        module.fail_json(msg='Module has failed! ('+results_of_execute_main[0]+')', **result)  
       

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
