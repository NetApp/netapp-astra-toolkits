#!/bin/bash

usage() {
  echo -e "\n"
  echo "Usage: $0 [ -a ASTRA_ACCOUNT_ID ] [ -t AUTHORIZATION_TOKEN ] [ -f ASTRA_FQDN ]" 1>&2
  echo "All options [-a, -t and -f] are required arguments"
  echo -e "\n"
}

exit_abnormal() {
  usage
  exit 1
}

while getopts ":a:t:f:h" options; do
  case "${options}" in
    a)
      ACCOUNT_ID=${OPTARG}
      ;;
    t)
      TOKEN=${OPTARG}
      ;;
    f)
      FQDN=${OPTARG}
      ;;
    h)
      exit_abnormal
      ;;
    :)
      echo "Error: -${OPTARG} requires an argument."
      exit_abnormal
      ;;
    *)
      exit_abnormal
      ;;
  esac
done

if [ -z "${ACCOUNT_ID}" ] || [ -z "${TOKEN}" ] || [ -z "${FQDN}" ]; then
  usage
  exit 1
fi

cat << EOF > netapp-astra-toolkits-2.0/config.yaml
headers:
  Authorization: Bearer ${TOKEN}
uid: ${ACCOUNT_ID}
astra_project: ${FQDN}
verifySSL: false
EOF

exit 0

