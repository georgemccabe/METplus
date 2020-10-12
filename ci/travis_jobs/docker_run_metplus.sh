#!/bin/bash

# set umask to 002 so that the travis user has (group) permission
# to move files that are created by docker

VOLUMES=$3
echo --Timing docker pull in docker_run_metplus...
start_seconds=$SECONDS

docker pull ${DOCKERHUB_TAG}

duration=$(( SECONDS - start_seconds ))
echo --TIMING docker_pull in docker_run_metplus $VOLUMES
echo "--TIMING docker pull ${DOCKERHUB_TAG} took $(($duration / 60)) minutes and $(($duration % 60)) seconds."

echo CURRENT_BRANCH = ${CURRENT_BRANCH}

echo 'In docker_run_metplus, $VOLUMES= ',$VOLUMES
echo 'DOCKER IMAGES in docker_run_metplus'
docker images


echo --Timing docker run in docker_run_metplus...
start_seconds=$SECONDS

echo  In docker_run_metplus.sh, RUNNING: $1
docker run --rm --user root:$UID $VOLUMES -v ${OWNER_BUILD_DIR}:${DOCKER_WORK_DIR} -v ${OWNER_BUILD_DIR}/output:${DOCKER_DATA_DIR}/output -v ${OWNER_BUILD_DIR}/input:${DOCKER_DATA_DIR}/input ${DOCKERHUB_TAG} /bin/bash -c "umask 002; $1"
ret=$?

duration=$(( SECONDS - start_seconds ))
echo --TIMING docker run in docker_run_metplus
echo "--TIMING docker run took $(($duration / 60)) minutes and $(($duration % 60)) seconds."

# check return codes
echo "In docker_run_metplus.sh previous return code: $2
echo "In docker_run_metplus.sh new return code: $ret

if [ $ret != 0 ]; then
  exit $ret
fi

exit $2
