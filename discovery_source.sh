#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#
echo "Executing ansible-playbook with discovery_source.yml file where oracle_source_dbname equals $1..."
ansible-playbook discovery_source.yml --module-path modules/ -i inventory --extra-vars "oracle_source_dbname=$1" 
