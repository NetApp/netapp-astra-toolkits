#!/bin/sh

# This variable is used for uniqueness across backup names, optionally change to a more preferred format
BACKUP_DESCRIPTION=$(date "+%Y%m%d%H%M%S")

# Error Codes
ebase=20
eusage=$((ebase+1))
eaccreate=$((ebase+4))
eaclist=$((ebase+5))
eacdestroy=$((ebase+6))
esnowticket=$((ebase+7))

file_sn_incident() {
    errmsg=$1
    app=$2
    curl "https://${snow_instance}/api/now/table/incident" \
        --request POST \
        --header "Accept:application/json" \
        --header "Content-Type:application/json" \
        --data "{'short_description': \"${app}: ${errmsg}\",'urgency':'2','impact':'2'}" \
        --user "${snow_username}":"${snow_password}"
    rc=$?
    if [ ${rc} -ne 0 ] ; then
        echo "--> Error creating ServiceNow incident with error message: ${errmsg}"
        exit ${esnowticket}
    fi
}

create_sn_event() {
    errmsg=$1
    app=$2
    curl "https://${snow_instance}/api/global/em/jsonv2" \
        --request POST \
        --header "Accept:application/json" \
        --header "Content-Type:application/json" \
        --user "${snow_username}":"${snow_password}" \
        --data @- << EOF
{
    "records": [
        {
            "source": "Instance Webhook",
            "node": "Astra Control",
            "resource": "${app}",
            "type":"Astra Control Disaster Recovery Issue",
            "severity":"3",
            "description":"${errmsg}",
            "additional_info": "{
                \"optional-key1\": \"optional-value1\",
                \"optional-key2\": \"optional-value2\"
            }"
        }
    ]
}
EOF
    rc=$?
    if [ ${rc} -ne 0 ] ; then
        echo "--> Error creating ServiceNow event with error message: ${errmsg}"
        exit ${esnowticket}
    fi
}

astra_create_backup() {
    app=$1
    echo "--> creating astra control backup"
    actoolkit create backup ${app} cron-${BACKUP_DESCRIPTION}
    rc=$?
    if [ ${rc} -ne 0 ] ; then
        ERR="error creating astra control backup cron-${BACKUP_DESCRIPTION} for ${app}"
        create_sn_event $ERR $app
        exit ${eaccreate}
    fi
}

astra_delete_backups() {
    app=$1
    backups_keep=$2

    echo "--> checking number of astra control backups"
    backup_json=$(actoolkit -o json list backups --app ${app})
    rc=$?
    if [ ${rc} -ne 0 ] ; then
        ERR="error running list backups for ${app}"
        create_sn_event $ERR $app
        exit ${eaclist}
    fi
    num_backups=$(echo $backup_json | jq  -r '.items[] | select(.state=="completed") | .id' | wc -l)

    while [ ${num_backups} -gt ${backups_keep} ] ; do

        echo "--> backups found: ${num_backups} is greater than backups to keep: ${backups_keep}"
        oldest_backup=$(echo ${backup_json} | jq '.items[] | select(.state=="completed")' | jq -s | jq -r 'min_by(.metadata.creationTimestamp) | .id')
        actoolkit destroy backup ${app} ${oldest_backup}
        rc=$?
        if [ ${rc} -ne 0 ] ; then
            ERR="error running destroy backup ${app} ${oldest_backup}"
            create_sn_event $ERR $app
            exit ${eacdestroy}
        fi

        sleep 120
        echo "--> checking number of astra control backups"
        backup_json=$(actoolkit -o json list backups --app ${app})
        rc=$?
        if [ ${rc} -ne 0 ] ; then
            ERR="error running list backups for ${app}"
            create_sn_event $ERR $app
            exit ${eaclist}
        fi
        num_backups=$(echo $backup_json | jq  -r '.items[] | select(.state=="completed") | .id' | wc -l)
    done

    echo "astra control backups at ${num_backups}"
}

#
# "main"
#
app_id=$1
backups_to_keep=$2
if [ -z ${app_id} ] || [ -z ${backups_to_keep} ] ; then
    echo "Usage: $0 <app_id> <backups_to_keep>"
    exit ${eusage}
fi

astra_create_backup ${app_id}
astra_delete_backups ${app_id} ${backups_to_keep}
