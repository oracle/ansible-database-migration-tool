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
module: oracle_cloud_odcb_module

short_description: This is Oracle Database Cloud Backup Module Installer

version_added: "1.0"

description:
    - "This module will help to install Oracle Database Cloud Backup Module"

options:
    opc_install_location:
        description:
            - This is a directory where opc_install.jar has been uploaded
        required: true
    host:
        description:
            - This is Oracle Object Storage Service URL.
        required: true
    opc_id:
        description:
            - OPC ID
        required: true
    opc_pass:
        description:
            - OPC Password
        required: true 
    container:
        description:
            - Container = OCI bucket
        required: true 
    wallet_dir:
        description:
            - Wallet directory
        required: true   
    lib_dir:
        description:
            - RMAN lib directory
        required: true
    config_file:
        description:
            - config file & directory
        required: true  
    proxy_host:
        description:
            - Proxy Host for HTTP access
        required: false
    proxy_port:
        description:
            - Proxy Port for HTTP access
        required: false 
    proxy_id:
        description:
            - Proxy User/Id for HTTP access
        required: false
    proxy_pass:
        description:
            - Proxy User/Id password for HTTP access
        required: false                     

'''

EXAMPLES = '''
# Install Oracle Database Cloud Backup Module
- name: Install Oracle Database Cloud Backup Module
  oracle_cloud_odcb_module:
    opc_install_location: '/tmp'
    host: 'https://swiftobjectstorage.<region>.oraclecloud.com/v1/<tenancy>'
    opc_id: '<firstname.lastname@example.com>'
    opc_pass: '<oci_auth_token_password>'
    container: '<oci_dbbackup_bucket>'
    wallet_dir: '/walletDirectory'
    lib_dir: '/libraryDirectory'
    config_file: '~/config'

'''

RETURN = '''
output_message:
    description: result of the execution
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




def setup_cloud_rman_module(opc_install_location, host, opc_id, opc_pass, container, wallet_dir, lib_dir, config_file, proxy_host, proxy_port, proxy_id, proxy_pass):


    args = ['java']
    args.append('-jar')
    args.append(os.path.join(opc_install_location, 'opc_install.jar'))
    args.append('-opcId')
    args.append(opc_id)
    args.append('-container')
    args.append(container)
    args.append('-walletDir')
    args.append(wallet_dir)
    args.append('-libDir')
    args.append(lib_dir)
    args.append('-configFile')
    args.append(config_file)
    args.append('-host')
    args.append(host)
    args.append('-opcPass')
    args.append(opc_pass)
    if proxy_host is not None:
        args.append('-proxyHost')
        args.append(proxy_host)
    if proxy_port is not None:
        args.append('-proxyPort')
        args.append(proxy_port)
    if proxy_id is not None:
        args.append('-proxyId')
        args.append(proxy_id)    
    if proxy_pass is not None:
        args.append('-proxyPass')
        args.append(proxy_pass)

    p = Popen(args, stdout=PIPE, stderr=PIPE, stdin=PIPE)    
    stdoutResult, stderrResult = p.communicate()

    return [stdoutResult.split('\n'),stderrResult,' '.join(args)]

def run_module():
    
    module_args = dict(
        opc_install_location=dict(type='str', required=True),
        host=dict(type='str', required=True),
        opc_id=dict(type='str', required=True),
        opc_pass=dict(type='str', required=True),
        container=dict(type='str', required=True),
        wallet_dir=dict(type='str', required=True),
        lib_dir=dict(type='str', required=True), 
        config_file=dict(type='str', required=True),  
        proxy_host=dict(type='str', required=False), 
        proxy_port=dict(type='str', required=False), 
        proxy_id=dict(type='str', required=False),
        proxy_pass=dict(type='str', required=False)          
    )

    result = dict(
        changed=False,
        output_message='',
        output_errors='',
        input_command='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    results_of_execute_cloud_rman_module = setup_cloud_rman_module(module.params['opc_install_location'],module.params['host'],module.params['opc_id'],module.params['opc_pass'],module.params['container'],module.params['wallet_dir'],module.params['lib_dir'],module.params['config_file'],module.params['proxy_host'],module.params['proxy_port'],module.params['proxy_id'],module.params['proxy_pass'])
    
    result['output_message'] = results_of_execute_cloud_rman_module[0]
    result['output_errors'] = results_of_execute_cloud_rman_module[1]
    result['input_command'] = results_of_execute_cloud_rman_module[2]

    if results_of_execute_cloud_rman_module.count('Download complete') != 0:
        module.fail_json(msg='Oracle Database Cloud Backup Module Installer has failed!', **result)    
    if results_of_execute_cloud_rman_module[1] != '':
        module.fail_json(msg='Oracle Database Cloud Backup Module Installer has failed!', **result) 
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
