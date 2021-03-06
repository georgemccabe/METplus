# set this to an empty string to use the working METPLUS_BASE
# set it to another METPLUS BASE location to test that version
export METPLUS_TEST_METPLUS_BASE=

# version of METplus to test
export METPLUS_TEST_MET_INSTALL_DIR=/usr/local/met-9.0
#export METPLUS_TEST_MET_INSTALL_DIR=/d1/CODE/MET/MET_releases/met-9.0_beta4
#export METPLUS_TEST_MET_INSTALL_DIR=/d1/CODE/MET/MET_development/MET-develop/met

# location to write output from test run
export METPLUS_TEST_OUTPUT_BASE=/d1/$USER/test-use-case-b

# location of output from previous test run to compare to current run
export METPLUS_TEST_PREV_OUTPUT_BASE=/d1/$USER/test-use-case-a

# location of input data to use in tests
export METPLUS_TEST_INPUT_BASE=/d1/METplus_Data

# location of GempakToCF to run tests that use Gempak
export METPLUS_TEST_GEMPAKTOCF_JAR=/d1/mccabe/bin/GempakToCF.jar
# Location of ncap2 exe
export METPLUS_TEST_NCAP2=/usr/local/nco/bin/ncap2

# Location of ncdump exe
export METPLUS_TEST_NCDUMP=/usr/local/netcdf/bin/ncdump
