#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#
ansible-playbook tests_after_setup.yml --module-path modules/ -i inventory --extra-vars @setup.json 

