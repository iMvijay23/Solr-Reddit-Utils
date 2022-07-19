#!/bin/bash

#############################
# Core and Data Path Settings
#
# Change variables as needed
# Run script from root directory
#############################
SCRIPT_HOME=$(pwd)
PORT=8983
CORE="FILL THIS"
SOLR_HOME="FILL THIS"
REDDIT_DATA="FILL THIS"
ENDPOINT="http://localhost:${PORT}/solr/${CORE}"
CORE_HOME="${SOLR_HOME}/server/solr/${CORE}"
CONFIG="${SCRIPT_HOME}/conf"
CREATE_CORE=false

# Create Solr core. Can also create it in Solr Admin page.
# Assumes Solr is running
#  solr start -m 5g
# https://stackoverflow.com/questions/25052139/adding-new-core-into-solr
# https://serverfault.com/questions/703031/how-do-i-add-a-solr-core-without-restarting-the-solr-server
# https://solr.apache.org/guide/6_6/indexconfig-in-solrconfig.html#IndexConfiginSolrConfig-IndexLocks
if ${CREATE_CORE}
then
  solr create -c ${CORE} -d "${CONFIG}"
  if [ $? -ne 0 ]
  then
      echo "Could not create core ${CORE}. Exiting."
      echo "If error says core 'already exists' run the following and try again:"
      echo "solr delete -c ${CORE}"
      exit 1
  else
      echo "Created core ${CORE} with endpoint ${ENDPOINT}"
  fi

  # Link the Solr settings to the repo
  # Easier for changing and saving the settings
  cd "${CORE_HOME}"
  echo "Config location: $CONFIG"
  rm -r conf
  ln -s "${CONFIG}" "conf"

  if [ $? -ne 0 ]
  then
      echo "Linking failed"
      exit 1
  else
      echo "Linked ${CORE_HOME}/conf to ${CONFIG}"
  fi

fi

# Load reddit data
cd ${SCRIPT_HOME}
python load_reddit_into_solr.py \
  --solr-endpoint "${ENDPOINT}" \
  --reddit-files "${REDDIT_DATA[@]}" \
  --jsonlines

