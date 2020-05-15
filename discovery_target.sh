#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#
echo "Executing ansible-playbook with discovery_target.yml file where oracle_target_dbname equals $1..."
ansible-playbook discovery_target.yml --module-path modules/ -i inventory --extra-vars "oracle_target_dbname=$1"

