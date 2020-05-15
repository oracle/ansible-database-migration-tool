#!/bin/bash
#
#Copyright (c) 2020, Oracle and/or its affiliates.
#The Universal Permissive License (UPL), Version 1.0
#

while getopts ":s:t:" opt; do
  case $opt in
    s) source_dbname="$OPTARG"
    ;;
    t) target_dbname="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

printf "Argument source_dbname is %s\n" "$source_dbname"
printf "Argument target_dbname is %s\n" "$target_dbname"

echo "Executing ansible-playbook with discovery_setup_json.yml file where oracle_source_dbname."
echo " "
if [ -z "$source_dbname" ]
then
  echo "1) oracle_source_dbname will be empty. Expecting only one ORACLE_HOME in oraInventory on the source (non Exadata environment)."
else
  echo "1) oracle_source_dbname has been set to $source_dbname. Script will try to extract ORACLE_HOME for this database (multihome, Exadata environment)."
fi

if [ -z "$target_dbname" ]
then
  echo "2) oracle_target_dbname will be empty. Expecting only one ORACLE_HOME in oraInventory on the target (non Exadata environment)."
else
  echo "2) oracle_target_dbname has been set to $target_dbname. Script will try to extract ORACLE_HOME for this database (multihome, Exadata environment)."
fi

ansible-playbook discovery_setup_json.yml --module-path modules/ -i inventory --extra-vars "oracle_source_dbname=$source_dbname oracle_target_dbname=$target_dbname" 

