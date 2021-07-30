Prerequisites:

        All the compute clusters are being managed by Astra.

       Install docker and docker run  -it jpaetzel0614/k8scloudcontrol:1.0 /bin/bash

       Clone the repo: git clone -b docker https://bitbucket.ngage.netapp.com/scm/~jpaetzel/netapp-astra-toolkits.git
       cd netapp-astra-toolkits

       Set up your kube config to successfully run kubectl commands

       Modify config.yaml to taste

"""
headers:
  Authorization: Bearer <TOKEN_CONTENTS>
uid: <REDACTED> # Get from the Astra UI
astra_project: preview # Used to generate the astra URL
"""

Run the following commands:

virtualenv toolkit
source toolkit/bin/activate
pip install -r requirements.txt

./toolkit.py deploy wordpress <appname> <namespacename>

This will deploy WordPress into the namespace <namespace> with the name
given by <appname>.
