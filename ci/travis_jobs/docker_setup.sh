echo Get Docker image: ${DOCKERHUB_TAG}
echo 'doing docker build'
# Note: adding --build-arg <arg-name> without any value tells docker to
#  use value from local environment (export DO_GIT_CLONE)

echo Timing docker pull in docker_setup.sh...
start_seconds=$SECONDS

docker pull ${DOCKERHUB_TAG} || true

duration1=$(( SECONDS - start_seconds ))
echo TIMING docker pull in docker_setup
echo "TIMING docker pull ${DOCKERHUB_TAG} took $(($duration1 / 60)) minutes and $(($duration1 % 60)) seconds."

echo CURRENT_BRANCH = ${CURRENT_BRANCH}


echo Timing docker build with --cache-from in docker_setup...
start_seconds=$SECONDS

docker build --pull --cache-from ${DOCKERHUB_TAG} -t ${DOCKERHUB_TAG} --build-arg SOURCE_BRANCH=${CURRENT_BRANCH} --build-arg MET_BRANCH=${DOCKERHUB_MET_TAGNAME} --build-arg DO_GIT_CLONE ${TRAVIS_BUILD_DIR}/ci/docker

duration2=$(( SECONDS - start_seconds ))
echo TIMING docker_build with --cache-from in docker_setup 
echo "TIMING docker build with cache-from took $(($duration2 / 60)) minutes and $(($duration2 % 60)) seconds."
echo

echo Timing docker push in docker_setup...
start_seconds=$SECONDS

echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin
docker push ${DOCKERHUB_TAG}

duration3=$(( SECONDS - start_seconds ))
echo TIMING docker_push in docker_setup
echo "TIMING docker push ${DOCKERHUB_TAG} took $(($duration3 / 60)) minutes and $(($duration3 % 60)) seconds."

duration_sum=$(( duration1 + duration2 + duration3 ))
echo "Total TIMING docker_setup ${DOCKERHUB_TAG} took $(($duration_sum / 60)) minutes and $(($duration_sum % 60)) seconds."
echo 

echo DOCKER IMAGES after DOCKER_SETUP
docker images
echo

echo 'done'
