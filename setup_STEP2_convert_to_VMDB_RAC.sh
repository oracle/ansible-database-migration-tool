#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#
ansible-playbook setup_STEP2_convert_to_VMDB_RAC.yml --module-path modules/ -i inventory --extra-vars @setup.json 

