# Test Use Cases in MET Tool Wrapper
# Author: George McCabe 05/2020
# Usage: test_use_case_met_tool_wrapper.sh
# About: Called by the .travis.yml file to run use cases found in parm/use_cases/met_tool_wrapper
# Note: Sample data tarball values must be updated if a new version is added to a release

source ${OWNER_BUILD_DIR}/METplus/internal_tests/use_cases/metplus_test_env.docker.sh
export TRAVIS_OUTPUT_BASE=${METPLUS_TEST_OUTPUT_BASE/$DOCKER_DATA_DIR/$OWNER_BUILD_DIR}
export TRAVIS_PREV_OUTPUT_BASE=${METPLUS_TEST_PREV_OUTPUT_BASE/$DOCKER_DATA_DIR/$OWNER_BUILD_DIR}

echo 'Owner Build Dir:' ${OWNER_BUILD_DIR}
echo 'pwd:' `pwd`
echo mkdir -p ${TRAVIS_PREV_OUTPUT_BASE}
mkdir -p ${TRAVIS_PREV_OUTPUT_BASE}
echo mkdir -p ${TRAVIS_OUTPUT_BASE}
mkdir -p ${TRAVIS_OUTPUT_BASE}

echo Running tests...
echo CURRENT_BRANCH = ${CURRENT_BRANCH}


echo Timing get_data_volumes in test_use_cases_met_tool_wrapper...
start_seconds=$SECONDS

VOLUMES=`${TRAVIS_BUILD_DIR}/ci/travis_jobs/get_data_volumes.py met_tool_wrapper`
duration1=$(( SECONDS - start_seconds ))
echo TIMING get_data_volumes in test_use_cases_met_tool_wrapper $VOLUMES
echo "TIMING docker get_data_volulmes took $(($duration1 / 60)) minutes and $(($duration1 % 60)) seconds."

# download GempakToCF.jar
${TRAVIS_BUILD_DIR}/ci/travis_jobs/download_gempaktocf.sh

echo Timing docker_run_metplus 1 in test_use_cases_met_tool_wrapper...
start_seconds=$SECONDS

returncode=0
echo 'Calling docker_run_metplus, returncode=' $returncode

${TRAVIS_BUILD_DIR}/ci/travis_jobs/docker_run_metplus.sh "${DOCKER_WORK_DIR}/METplus/internal_tests/use_cases/run_test_use_cases.sh docker --met_tool_wrapper" $returncode "$VOLUMES"
returncode=$?

duration2=$(( SECONDS - start_seconds ))
echo TIMING docker_run_metplus in test_use_cases_met_tool_wrapper
echo "TIMING docker docker_run_metplus 1 took $(($duration2 / 60)) minutes and $(($duration2 % 60)) seconds."

echo 'Intermediate return code=' $returncode 

rm -rf ${TRAVIS_OUTPUT_BASE}/logs
mv ${TRAVIS_OUTPUT_BASE}/* ${TRAVIS_PREV_OUTPUT_BASE}/

echo Timing docker_run_metplus 2 in test_use_cases_met_tool_wrapper...
start_seconds=$SECONDS

${TRAVIS_BUILD_DIR}/ci/travis_jobs/docker_run_metplus.sh "pip3 install h5py; ${DOCKER_WORK_DIR}/METplus/internal_tests/use_cases/run_test_use_cases.sh docker --config met_tool_wrapper/PCPCombine/PCPCombine_python_embedding.conf,user_env_vars.MET_PYTHON_EXE=python3" $returncode "$VOLUMES"
returncode=$?

duration3=$(( SECONDS - start_seconds ))
echo TIMING docker_run_metplus 2 in test_use_cases_met_tool_wrapper $VOLUMES
echo "TIMING docker docker_run_metplus 2 took $(($duration3 / 60)) minutes and $(($duration3 % 60)) seconds."

echo '2nd Intermediate return code=' $returncode 

rm -rf ${TRAVIS_OUTPUT_BASE}/logs
mv ${TRAVIS_OUTPUT_BASE}/* ${TRAVIS_PREV_OUTPUT_BASE}/

echo Timing docker_run_metplus 3 in test_use_cases_met_tool_wrapper...
start_seconds=$SECONDS

### put cyclone plotter with cartopy and matplotlib
${TRAVIS_BUILD_DIR}/ci/travis_jobs/docker_run_metplus.sh "${DOCKER_WORK_DIR}/METplus/ci/travis_jobs/get_cartopy.sh; pip3 install matplotlib; export DISPLAY=localhost:0.0; ${DOCKER_WORK_DIR}/METplus/internal_tests/use_cases/run_test_use_cases.sh docker --config met_tool_wrapper/CyclonePlotter/CyclonePlotter.conf,user_env_vars.MET_PYTHON_EXE=python3" $returncode "$VOLUMES"
returncode=$?

duration4=$(( SECONDS - start_seconds ))
echo TIMING docker_run_metplus 2test_use_cases_met_tool_wrapper $VOLUMES
echo "TIMING docker docker_run_metplus 3 took $(($duration4 / 60)) minutes and $(($duration4 % 60)) seconds."

duration_sum = $(( duration1 + duration2 + duration3 + duration4 ))
echo "Total TIMING test_ues_cases_met_tool_wrapper took $(($duration_sum / 60)) minutes and $(($duration_sum % 60)) seconds."
echo 'Final return code=' $returncode 

rm -rf ${TRAVIS_OUTPUT_BASE}/logs
mv ${TRAVIS_OUTPUT_BASE}/* ${TRAVIS_PREV_OUTPUT_BASE}/

echo Tests completed.

# Dump the output directories from running METplus
#echo listing TRAVIS_OUTPUT_BASE
#ls -alR ${TRAVIS_OUTPUT_BASE}

#echo
#echo listing TRAVIS_PREV_OUTPUT_BASE
#ls -alR ${TRAVIS_PREV_OUTPUT_BASE}

# Dump and see how much space is left on Travis disk.
df -h

exit $returncode
