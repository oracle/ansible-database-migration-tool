#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#
ansible-playbook setup_STEP1b_convert_to_CDB.yml --module-path modules/ -i inventory --extra-vars @setup.json --extra-vars @noncdb_2_cdb.json -vvv --step

