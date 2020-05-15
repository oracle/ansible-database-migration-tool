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
module: oracle_dbcli_module

short_description: This is simple DBCLI module for remote execution

version_added: "1.0"

description:
    - "This module will help to pickup some answers from DBCLI exectution"

options:
    dbcli_command:
        description:
            - Main dbcli command
        required: true
    object_store_swift_name:  
        description:
            - Main dbcli create-objectstoreswift (...) -name <object_store_swift_name> (...)
        required: false     
    object_store_swift_tenant_name:       
        description:
            - Main dbcli create-objectstoreswift (...) -tenantname <object_store_swift_tenant_name> (...)
        required: false 
    object_store_swift_user_name:
        description:
            - Main dbcli create-objectstoreswift (...) -username <object_store_swift_user_name> (...)
        required: false 
    object_store_swift_endpointurl:
        description:
            - Main dbcli create-objectstoreswift (...) -endpointurl <object_store_swift_endpointurl> (...)
        required: false
    object_store_swift_user_pass:
        description:
            - Main dbcli create-objectstoreswift (...) -hp <object_store_swift_user_pass>
        required: false 
    db_backup_destination:
        description:
            - Main dbcli create-backupconfig (...) --backupdestination <db_backup_destination> (...)
        required: false 
    db_backup_container:
        description:
            - Main dbcli create-backupconfig (...) --container <db_backup_container> (...)
        required: false 
    db_backup_objectstoreswiftId 
        description:
            - Main dbcli create-backupconfig (...) --objectstoreswiftId <db_backup_objectstoreswiftId> (...)
        required: false  
    db_backup_recoverywindow    
        description:
            - Main dbcli create-backupconfig (...) --recoverywindow <db_backup_recoverywindow> (...)
        required: false  
    db_backup_name
        description:
            - Main dbcli create-backupconfig (...) --name <db_backup_name> (...)
        required: false 
    db_storage_dbname
        description:
            - Main dbcli create-dbstorage (...) --dbname <db_storage_dbname> (...)
        required: false
    db_storage_databaseUniqueName
        description:
            - Main dbcli create-dbstorage (...) --databaseUniqueName <databaseUniqueName> (...)
        required: false
    db_storage_dbstorage
        description:
            - Main dbcli create-dbstorage (...) --dbstorage <db_storage_dbstorage> (...)
        required: false
    register_database_dbclass
        description:
            - Main dbcli register-database (...) --dbclass <register_database_dbclass> (...)
        required: false
    register_database_dbshape
        description:
            - Main dbcli register-database (...) --dbshape <register_database_dbshape> (...)
        required: false                   
    register_database_servicename
        description:
            - Main dbcli register-database (...) --servicename <register_database_servicename> (...)
        required: false       
    register_database_backupconfigid
        description:
            - Main dbcli register-database (...) --backupconfigid <register_database_backupconfigid> (...)
        required: false       
    register_database_syspassword
        description:
            - Main dbcli register-database (...) --syspassword <register_database_syspassword> (...)
        required: false              

'''

EXAMPLES = '''
# Execute dbcli remotely on OCI dbnode
- name: Execute dbcli create-objectstoreswift  
  become: yes 
  become_method: sudo   
  oracle_dbcli_module:
    dbcli_command: 'create-objectstoreswift'
    object_store_swift_name: '<backup_of_db_bucket>'
    object_store_swift_tenant_name: '<oci_tenancy>'
    object_store_swift_user_name: '<firstname.lastname@example.com>'
    object_store_swift_endpointurl: 'https://swiftobjectstorage.<oci_region>.oraclecloud.com/v1'
    object_store_swift_user_pass: '<xxxxxxMYPASSWORD>'

- name: Execute dbcli create-backupconfig  
  become: yes
  become_method: sudo   
  oracle_dbcli_module:
    dbcli_command: 'create-backupconfig'
    db_backup_destination: 'OBJECTSTORE'
    db_backup_container: '<backup_of_db_bucket>'
    db_backup_objectstoreswiftId: '46f9d080-f401-4a0f-a23a-97b7ea3200d1'
    db_backup_recoverywindow: '30'
    db_backup_name: 'backup_of_database'

- name: Execute dbcli create-dbstorage  
  become: yes
  become_method: sudo   
  oracle_dbcli_module:
    dbcli_command: 'create-dbstorage'
    db_storage_dbname: 'SRC12'
    db_storage_databaseUniqueName: 'SRC12'
    db_storage_dbstorage: 'ASM'

- name: Execute dbcli register-database  
  become: yes
  become_method: sudo    
  oracle_dbcli_module:
    dbcli_command: 'register-database'
    register_database_dbclass: 'OLTP'
    register_database_dbshape: 'odb1'
    register_database_servicename: 'SRC12.<oci_subnet>.<oci_tenancy>vcn.oraclevcn.com'
    register_database_backupconfigid: '2165b0aa-06b0-40ec-ab8d-b30f8560ddb6'
    register_database_syspassword: '<sys_passowrd>'
    
'''

RETURN = '''
dbcli_message:
    description: JSON result of DBCLI execution.
    type: str
changed:
    description: will be used for the future all removed.
    type: bool   
'''

from ansible.module_utils.basic import AnsibleModule
from subprocess import Popen, PIPE
from tempfile import mkstemp, TemporaryFile
from datetime import datetime, timedelta
import os, sys, re, json


def execute_dbcli(dbcli_command, 
    object_store_swift_name, 
    object_store_swift_tenant_name, 
    object_store_swift_user_name, 
    object_store_swift_endpointurl, 
    object_store_swift_user_pass, 
    object_store_swift_id, 
    db_backup_destination, 
    db_backup_container, 
    db_backup_objectstoreswiftId, 
    db_backup_recoverywindow, 
    db_backup_name, 
    db_backup_id, 
    db_backup_backupconfigname, 
    db_storage_dbname, 
    db_storage_databaseUniqueName, 
    db_storage_dbstorage, 
    register_database_dbclass, 
    register_database_dbshape, 
    register_database_servicename, 
    register_database_backupconfigid, 
    register_database_syspassword, 
    db_id, 
    create_backup_backup_type,
    create_backup_component,
    create_backup_longterm_keep_days,
    create_backup_tag,
    as_json):

    args = [os.path.join('/opt/oracle/dcs/bin','dbcli')]
    
    args.append(dbcli_command)
    
    if object_store_swift_name is not None:
        args.append('--name')
        args.append(object_store_swift_name)

    if object_store_swift_tenant_name is not None:
        args.append('--tenantname')
        args.append(object_store_swift_tenant_name)

    if object_store_swift_user_name is not None:
        args.append('--username')
        args.append(object_store_swift_user_name)    

    if object_store_swift_endpointurl is not None:
        args.append('--endpointurl')
        args.append(object_store_swift_endpointurl)        
    
    if object_store_swift_user_pass is not None:
        args.append('-hp')
        args.append(object_store_swift_user_pass) 
    
    if object_store_swift_id is not None:
        args.append('--objectstoreswiftid')
        args.append(object_store_swift_id)

    if db_backup_destination is not None: 
        args.append('--backupdestination')
        args.append(db_backup_destination)

    if db_backup_container is not None:
        args.append('--container')
        args.append(db_backup_container)

    if db_backup_objectstoreswiftId is not None:
        args.append('--objectstoreswiftId')
        args.append(db_backup_objectstoreswiftId)

    if db_backup_recoverywindow is not None:
        args.append('--recoverywindow')
        args.append(db_backup_recoverywindow)

    if db_backup_name is not None: 
        args.append('--name')
        args.append(db_backup_name)

    if db_backup_id is not None:
        args.append('--id')
        args.append(db_backup_id)   

    if db_backup_backupconfigname is not None:
        args.append('--backupconfigname')
        args.append(db_backup_backupconfigname) 

    if db_storage_dbname is not None: 
        args.append('--dbname')
        args.append(db_storage_dbname)

    if db_storage_databaseUniqueName is not None: 
        args.append('--databaseUniqueName')
        args.append(db_storage_databaseUniqueName)

    if db_storage_dbstorage is not None: 
        args.append('--dbstorage')
        args.append(db_storage_dbstorage)

    if register_database_dbclass is not None: 
        args.append('--dbclass')
        args.append(register_database_dbclass)
        
    if register_database_dbshape is not None:
        args.append('--dbshape') 
        args.append(register_database_dbshape)

    if register_database_servicename is not None:
        args.append('--servicename') 
        args.append(register_database_servicename)

    if register_database_backupconfigid is not None:
        args.append('--backupconfigid')
        args.append(register_database_backupconfigid)

    if db_id is not None:
        args.append('--dbid')
        args.append(db_id)   

    if create_backup_backup_type is not None:
        args.append('--backupType')
        args.append(create_backup_backup_type) 

    if create_backup_component is not None:
        args.append('--component')
        args.append(create_backup_component) 

    if create_backup_longterm_keep_days is not None:
        args.append('--keepDays')
        args.append(create_backup_longterm_keep_days) 

    if create_backup_tag is not None:
        args.append('--tag')
        args.append(create_backup_tag) 

    if as_json is True:
        args.append('--json')

    if register_database_syspassword is not None:
        args.append('--syspassword')    

    my_env = os.environ.copy()
    
    p = Popen(args, stdout=PIPE, stderr=PIPE, env=my_env, stdin=PIPE)    
    
    if register_database_syspassword is not None:
        p.stdin.write(register_database_syspassword.encode())    

    stdoutResult, stderrResult = p.communicate()    
    
    return [stdoutResult,stderrResult,' '.join(args)]

def run_module():
    
    module_args = dict(
        dbcli_command=dict(type='str', required=True),
        object_store_swift_name=dict(type='str', required=False),
        object_store_swift_tenant_name=dict(type='str', required=False),
        object_store_swift_user_name=dict(type='str', required=False),
        object_store_swift_endpointurl=dict(type='str', required=False),
        object_store_swift_user_pass=dict(type='str', required=False),
        object_store_swift_id=dict(type='str', required=False),
        db_backup_destination=dict(type='str', required=False),
        db_backup_container=dict(type='str', required=False),
        db_backup_objectstoreswiftId=dict(type='str', required=False),
        db_backup_recoverywindow=dict(type='str', required=False),
        db_backup_name=dict(type='str', required=False),
        db_backup_id=dict(type='str', required=False),
        db_backup_backupconfigname=dict(type='str', required=False),
        db_storage_dbname=dict(type='str', required=False),
        db_storage_databaseUniqueName=dict(type='str', required=False),
        db_storage_dbstorage=dict(type='str', required=False),
        register_database_dbclass=dict(type='str', required=False),
        register_database_dbshape=dict(type='str', required=False),
        register_database_servicename=dict(type='str', required=False),
        register_database_backupconfigid=dict(type='str', required=False),
        register_database_syspassword=dict(type='str', required=False),
        db_id=dict(type='str', required=False),
        create_backup_backup_type=dict(type='str', required=False),
        create_backup_component=dict(type='str', required=False),
        create_backup_longterm_keep_days=dict(type='str', required=False),
        create_backup_tag=dict(type='str', required=False),
        as_json=dict(type='bool', required=False, default=True),
        ignore_DCS_errors=dict(type='bool', required=False, default=False),

    )

    result = dict(
        changed=False,
        dbcli_output='',
        dbcli_error='',
        dbcli_command='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_dbcli = execute_dbcli(
        module.params['dbcli_command'],
        module.params['object_store_swift_name'],
        module.params['object_store_swift_tenant_name'],
        module.params['object_store_swift_user_name'],
        module.params['object_store_swift_endpointurl'],
        module.params['object_store_swift_user_pass'],
        module.params['object_store_swift_id'],
        module.params['db_backup_destination'],
        module.params['db_backup_container'],
        module.params['db_backup_objectstoreswiftId'],
        module.params['db_backup_recoverywindow'],
        module.params['db_backup_name'],
        module.params['db_backup_id'],
        module.params['db_backup_backupconfigname'],
        module.params['db_storage_dbname'],
        module.params['db_storage_databaseUniqueName'],
        module.params['db_storage_dbstorage'],
        module.params['register_database_dbclass'],
        module.params['register_database_dbshape'],
        module.params['register_database_servicename'],
        module.params['register_database_backupconfigid'],
        module.params['register_database_syspassword'],
        module.params['db_id'],
        module.params['create_backup_backup_type'],
        module.params['create_backup_component'],
        module.params['create_backup_longterm_keep_days'],
        module.params['create_backup_tag'],
        module.params['as_json']      
        )
    
    if module.params['as_json'] is True:
        # DCS-10032:Resource backup config is not found.
        try:
            result['dbcli_output'] = json.loads(results_of_execute_dbcli[0])
        except ValueError:
            result['dbcli_output'] = ''    
    else:
        result['dbcli_output'] = results_of_execute_dbcli[0]

    result['dbcli_error'] = results_of_execute_dbcli[1]
    result['dbcli_command'] = results_of_execute_dbcli[2]

    if results_of_execute_dbcli[1] != '':
        if module.params['ignore_DCS_errors'] == 'False':   
            module.fail_json(msg='DBCLI module has failed!', **result)    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
