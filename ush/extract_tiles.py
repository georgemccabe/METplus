#!/usr/bin/env python

'''
Program Name: extract_tiles.py
Contact(s): Julie Prestopnik, Minna Win
Abstract: Extracts tiles to be used by series_analysis History Log:  Initial version 
Usage: extract_tiles.py
Parameters: None
Input Files: tc_pairs data
Output Files: tiled grib2 files
Condition codes: 0 for success, 1 for failure

'''

from __future__ import (print_function, division )

import constants_pdef as P
import logging
import os
import sys
import met_util as util
import time
import re
import subprocess
import string_template_substitution as sts
import run_tc_stat as tcs

def main():
    '''Get TC-pairs track data and GFS model data, do any necessary processing then
       regrid the forecast and analysis files to a 30x 30 degree tile centered on the
       storm.
      
       Args:
           None 

       Returns:

           None: invokes wgrib2 to create a new grib file from two extratropical storm track files.

    '''

    # Retrieve parameters from corresponding param file
   
    cur_filename = sys._getframe().f_code.co_filename
    cur_function = sys._getframe().f_code.co_name
    init_times = p.opt["INIT_LIST"]
    output_dir = p.opt["OUT_DIR"]
    project_dir = p.opt["PROJ_DIR"]
    overwrite_flag = p.opt["OVERWRITE_TRACK"]
    addl_filter_opts = p.opt["EXTRACT_TILES_FILTER_OPTS"]
    filtered_out_dir = p.opt["EXTRACT_OUT_DIR"]
    tc_stat_exe = p.opt["TC_STAT"]


    # get the process id to be used to identify the output
    # amongst different users and runs.
    cur_pid = str(os.getpid())
    tmp_dir = os.path.join(p.opt["TMP_DIR"], cur_pid)
   
    # Logging output: TIME UTC |TYPE (DEBUG, INFO, WARNING, etc.) |
    # [File : function]| Message logger.info("INFO |  [" + 
    # cur_filename +  ":" + "cur_function] |" + "BEGIN extract_tiles")
    
    # Process TC pairs by initialization time
    for cur_init in init_times:
        msg = ("INFO| [" + cur_filename + ":" + cur_function +  
               " ] |Begin processing for initialization time: " + cur_init)
        logger.info(msg)
        year_month = util.extract_year_month(cur_init, logger)
        
       # Create the name of the filter file we need to find.  If 
       # the file doesn't exist, then run TC_STAT 
        filter_filename = "filter_" + cur_init + ".tcst"
        filter_name = os.path.join(filtered_out_dir, cur_init, filter_filename)

        if util.file_exists(filter_name) and overwrite_flag == False:
            msg = ("INFO| [" + cur_filename + ":" + cur_function +  
                   " ] | Filter file exists, using Track data file: " + 
                   filter_name)
            logger.info(msg)
        else:
           # Create the storm track
            filter_path = os.path.join(filtered_out_dir, cur_init)
            util.mkdir_p(filter_path)
            tc_cmd_list = [tc_stat_exe, " -job filter -lookin ", 
                           project_dir,"/tc_pairs/", year_month, 
                           " -init_inc ", cur_init, 
                           " -match_points true -dump_row ", 
                           filter_name, " ", addl_filter_opts]

            # Perform any filtering by calling run_tc_stat
            tc_cmd = ''.join(tc_cmd_list)
            tcs.tc_stat(p, logger, tc_cmd, 
                        filtered_out_dir)
            msg = ("INFO| [" + cur_filename + ":" + cur_function +  
                   " ] | tc command: " + tc_cmd)
            logger.info(msg)
            
        # Now get unique storm ids from the filter file, 
        # filter_yyyymmdd_hh.tcst
        sorted_storm_ids = get_storm_ids(filter_name, logger)
       
        # Process each storm in the sorted_storm_ids list
        # Iterate over each filter file in the output directory and 
        # search for the presence of the storm id.  Store this 
        # corresponding row of data into a temporary file in the 
        # /tmp/<pid> directory.
       
        storm_match_list = [] 
        for cur_storm in sorted_storm_ids:
            msg = ("INFO| [" + cur_filename + ":" + cur_function +  
                   " ] | Processing storm: " + cur_storm)
            logger.info(msg)
            storm_output_dir = os.path.join(filtered_out_dir,cur_init, 
                                            cur_storm)
            util.mkdir_p(storm_output_dir)
            util.mkdir_p(tmp_dir)
            tmp_file = "filter_" + cur_init + "_" + cur_storm
            tmp_filename = os.path.join(tmp_dir, tmp_file)
            
            storm_match_list = util.grep(cur_storm, filter_name)
            with open(tmp_filename, "a+") as tmp_file:
               for storm_match in storm_match_list:
                   tmp_file.write(storm_match)
               
            # Peform regridding of the forecast and analysis files 
            # to a 30 x 30 degree tile centered on the storm
            regrid_fcst_anly(tmp_filename, cur_init, cur_storm, logger, p)

        # end of for cur_storm 

    # end of for cur_init

    # Clean up the tmp directory
    subprocess.call(["rm", "-rf", tmp_dir])



def regrid_fcst_anly(tmp_filename, cur_init, cur_storm, logger, p):
    ''' Create the analysis tile and forecast file names from the 
        temp filter file in the /tmp directory. Then perform
        regridding 
   
        Args:
        tmp_filename:      Filename of the temporary filter file in 
                           the /tmp directory which contains rows 
                           of data corresponding to a storm id of varying
                           lead times.

        cur_init:          The current init time
     
        cur_storm:         The current storm 

        logger     :       The name of the logger used in logging.
        p          :       ConfigMaster constants file
     
        Returns:
        None:              Performs regridding via invoking wgrib2 
                           on the forecast and analysis files to 
                           a 30 x 30 degree tile centered on the storm:
                           latlon lon0:nlon:dlon lat0:nlat:dlat
                           NOTE:  the values for nlon, dlon and lat and 
                                  lon adjustment values are stored in 
                                  the extract_tiles_parm parameter/config 
                                  file.

    '''

    # Extract the columns of interest: init time, lead time, 
    # valid time lat and lon of both  tropical cyclone tracks, etc. 
    # Then calculate the forecast hour and other things.
   
    cur_filename = sys._getframe().f_code.co_filename
    cur_function = sys._getframe().f_code.co_name
    gfs_dir = p.opt["GFS_DIR"]
    output_dir = p.opt["OUT_DIR"]
    wgrib2_exe = p.opt["WGRIB2"]
    egrep_exe = p.opt["EGREP_EXE"]
    requested_records = p.opt["GRIB2_RECORDS"]
    filtered_out_dir = p.opt["EXTRACT_OUT_DIR"]

    # obtain the gfs_fcst dir
    with open(tmp_filename, "r") as tf:
        for line in tf:
            col = line.split()
            # Columns of interest are 8, 9, 10, 19, 20, 21, and 22
            # for init time, lead time, valid time, alat, alon, 
            # blat, and blon (positions of the two extra-tropical
            # cyclone tracks)  but Python is zero-based so indices 
            # differ by 1.
            init, lead, valid, alat, alon, blat, blon = col[7], col[8], col[9],                                                         col[18], col[19],                                                               col[20], col[21]

            # integer division for both Python 2 and 3
            lead_time = int(lead)
            fcst_hr = lead_time // 10000
            fcst_hr_str = str(fcst_hr)

            init_ymd_match = re.match(r'[0-9]{8}',init)
            if init_ymd_match:
                init_ymd = init_ymd_match.group(0)
            else:
                raise RuntimeError('init time has unexpected format for YMD')
                logger.WARN("RuntimeError raised")

            init_ymdh_match = re.match(r'[0-9|_]{11}',init)
            if init_ymdh_match:
                init_ymdh = init_ymdh_match.group(0)
            else:
                logger.WARN("RuntimeError raised")
                #raise RuntimeError('init time has unexpected format for YMDH')

            valid_ymd_match = re.match(r'[0-9]{8}',valid)
            if valid_ymd_match:
                valid_ymd = valid_ymd_match.group(0)
            else:
                logger.WARN("RuntimeError raised")
                #raise RuntimeError('valid time has unexpected format for YMD')

            valid_ymdh_match = re.match(r'[0-9|_]{11}',valid)
            if valid_ymdh_match:
                valid_ymdh = valid_ymdh_match.group(0)
            else:
                logger.WARN("RuntimeError raised")
                #raise RuntimeError('valid time has unexpected format for YMDH')

                
            lead_str = str(fcst_hr).zfill(3)
                
            fcst_dir = os.path.join(gfs_dir, init_ymd)
            init_ymdh_split = init_ymdh.split("_")
            init_YYYYmmddHH = "".join(init_ymdh_split)
            fcstSTS = sts.StringTemplateSubstitution(logger,
                                                     p.opt["GFS_FCST_FILE_TMPL"]                                                     , init=init_YYYYmmddHH, 
                                                     lead=lead_str)

            fcst_file = fcstSTS.doStringSub()
            fcst_filename = os.path.join(fcst_dir, fcst_file)

            anly_dir =  os.path.join(gfs_dir, valid_ymd)
            valid_ymdh_split = valid_ymdh.split("_")
            valid_YYYYmmddHH = "".join(valid_ymdh_split)
            anlySTS = sts.StringTemplateSubstitution(logger, 
                                                     p.opt["GFS_ANLY_FILE_TMPL"]                                                     , valid=valid_YYYYmmddHH,
                                                     lead=lead_str)
            anly_file = anlySTS.doStringSub()
            anly_filename = os.path.join(anly_dir, anly_file)
            
            # Create the tmp file to be used for troubleshooting 
            # and verification.  The file will contain all the 
            # fcst and analysis files that will be used as input 
            # for another script.
            tmp_fcst_filename = os.path.join(filtered_out_dir, 
                                             "tmp_fcst_regridded.txt")
            tmp_anly_filename = os.path.join(filtered_out_dir, 
                                             "tmp_anly_regridded.txt")

            # Check if the forecast file exists. If it doesn't 
            # exist, just log it
            if util.file_exists(fcst_filename):
                msg = ("INFO| [" + cur_filename + ":" + cur_function +  
                       " ] | Forecast file: " + fcst_filename)
                logger.info(msg)
                # Write this to the tmp file (to be used for 
                # troubleshooting and validation) which will be saved
                # in the EXTRACT_OUT_DIR
                with open(tmp_fcst_filename, "a+") as tmpfile:
                    tmpfile.write(fcst_filename+"\n")
                
            else:
                msg = ("WARNING| [" + cur_filename + ":" + 
                       cur_function +  " ] | " +
                       "Can't find forecast file, continuing anyway: " + 
                       fcst_filename)
                logger.warn(msg)
                continue

            # Check if the analysis file exists. If it doesn't 
            # exist, just log it.
            if util.file_exists(anly_filename):
                    msg = ("INFO| [" + cur_filename + ":" +
                           cur_function +  " ] | Analysis file: " + 
                           anly_filename)
                    logger.info(msg)
                    # Write this to the tmp file (to be used for 
                    # troubleshooting and validation). This will
                    # be stored in the EXTRACT_OUT_DIR
                    with open(tmp_anly_filename, "a+") as tmpfile:
                        tmpfile.write(fcst_filename+"\n")
            else:
                msg = ("WARNING| [" + cur_filename + ":" + 
                       cur_function +  " ] | " + 
                       "Can't find analysis file, continuing anyway: " +
                       anly_filename)
                logger.warn(msg)
                continue

            # Regrid the forecast and analysis files to an n degree X 
            # m degree tile centered on
            # latlon lon0:nlon:dlon lat0:nlat:dlat
            # The size of the grid is defined in the constants_pdef.py
            # param/config file, under the LON_ADJ and LAT_ADJ 
            # variables.
        
            fcst_base = os.path.basename(fcst_filename)
            anly_base = os.path.basename(anly_filename)
            fcst_tile_grid = create_tile_grid_string(alat,alon,logger,p)
            anly_tile_grid = create_tile_grid_string(blat,blon,logger,p)
 
            tile_dir = os.path.join(filtered_out_dir, cur_init, cur_storm)
            fcst_hr_str = str(fcst_hr).zfill(3)
            
            fcst_tile_filename = p.opt["FCST_TILE_PREFIX"] + fcst_hr_str                                         + "_" + fcst_base
            fcst_tile_file = os.path.join(tile_dir, fcst_tile_filename)
            anly_tile_filename =  p.opt["ANLY_TILE_PREFIX"] + fcst_hr_str                                         + "_" + anly_base
            anly_tile_file = os.path.join(tile_dir, anly_tile_filename)
            
            # Regrid via wgrib2 on the fcst file only if a fcst tile 
            # file does NOT already exist.

            # Create new gridded file for fcst tile
            if util.file_exists(fcst_tile_file):
                msg = ("INFO| [" + cur_filename + ":" + 
                       cur_function +  " ] | Forecast tile file " + 
                       fcst_tile_file + " exists, skip wgrib2 regridding")
                logger.info(msg)
            else:
                # Invoke wgrb2 to perform regridding on the records of interest
                fcst_cmd_list= [wgrib2_exe, ' ' , fcst_filename, ' | ', 
                                egrep_exe, ' "',requested_records, '"|', 
                                wgrib2_exe, ' -i ', fcst_filename,
                                ' -new_grid ', fcst_tile_grid, ' ', 
                                fcst_tile_file]
                wgrb_cmd_fcst = ''.join(fcst_cmd_list)
                msg = ("INFO|[wgrib2]| Regridding via wgrib2:" + 
                       wgrb_cmd_fcst)
                logger.info(msg)
                wgrb_fcst_out = subprocess.check_output(wgrb_cmd_fcst, 
                                                        stderr=
                                                        subprocess.STDOUT, 
                                                        shell=True)
                logger.info("INFO|[wgrib2]| on fcst file:" + wgrb_fcst_out)
            
            # Create new gridded file for anly tile
            if util.file_exists(anly_tile_file):
                logger.info("INFO| [" + cur_filename + ":" + 
                            cur_function +  " ] | Analysis tile file: " + 
                            anly_tile_file + " exists, skip wgrib2 regridding")
            else:
                # Invoke wgrb2 to perform regridding on the records of interest
                anly_cmd_list= [wgrib2_exe, ' ' , anly_filename, ' | ', 
                                egrep_exe, ' "', requested_records, '"|',
                                wgrib2_exe, ' -i ', anly_filename, 
                                ' -new_grid ', anly_tile_grid, ' ', 
                                anly_tile_file, '>/dev/null']
                wgrb_cmd_anly = ''.join(anly_cmd_list)
                wgrb_anly_out = subprocess.check_output(wgrb_cmd_anly, 
                                                        stderr=
                                                        subprocess.STDOUT, 
                                                        shell=True)
                logger.info("INFO|[wgrib2]| on analysis file:" + wgrb_anly_out)


def get_storm_ids(filter_filename, logger):
    ''' Get each storm as identified by its STORM_ID in the filter file 
        save these in a set so we only save the unique ids and sort them.
     
        Args:
            filter_filename (string):  The name of the filter file to read 
                                       and extract the storm id   
            logger (string):  The name of the logger for logging useful info

        Returns:
            sorted_storms (List):  a list of unique, sorted storm ids
    '''
    cur_filename = sys._getframe().f_code.co_filename
    cur_function = sys._getframe().f_code.co_name
    storm_id_list = set()
    if os.path.isfile(filter_filename) and                                             os.path.getsize(filter_filename) > 0:
        with open(filter_filename) as fileobj:
             # skip the first line as it contains the header
             try:
                 next(fileobj)
             except StopIteration,e:
                 return storm_id_list
             for line in fileobj:
                 # split the columns, which are separated by one or
                 # more whitespace, hence the line.split() without any
                 # args
                 cols = line.split()

                 # we are only interested in the 4th column, STORM_ID
                 storm_id_list.add(str(cols[3]))

    else:
        return storm_id_list

    # sort the unique storm ids
    sorted_storms  = sorted(storm_id_list)
    return sorted_storms



def create_tile_grid_string(lat,lon,logger,p):
     ''' Create the tile grid string that has the format:
         latlon lon0:nlon:dlon lat0:nlat:dlat

         Args:
            lat (string):  the latitude of the grid point
            lon (string):  the longitude of the grid point
            logger(string): The name of the logger
            p      : ConfigMaster constants file

         Returns:
            tile_grid_str (string): the tile grid string for the
                                    input lon and lat

      '''
 
     cur_filename = sys._getframe().f_code.co_filename
     cur_function = sys._getframe().f_code.co_name

     # initialize the tile grid string
     # and get the other values from the parameter file
     tile_grid_str = ' '
     lon_subtr = p.opt["LON_ADJ"]
     adj_lon = float(lon) - lon_subtr
     lat_subtr = p.opt["LAT_ADJ"]
     adj_lat = float(lat) - lat_subtr
     nlat = str(p.opt["NLAT"])
     nlon = str(p.opt["NLON"])
     dlat = str(p.opt["DLAT"])
     dlon = str(p.opt["DLON"])
  

     adj_lon = float(lon) - lon_subtr
     adj_lat = float(lat) - lat_subtr


     lon0 = str(util.round_0p5(adj_lon))
     lat0 = str(util.round_0p5(adj_lat))

     #Format is: latlon lon0:nlon:dlat lat0:nlat:dlat
     grid_list = ['latlon ', lon0, ':', nlon, ':', dlon, ' ',  
                  lat0, ':', nlat, ':', dlat]
     tile_grid_str = ''.join(grid_list)
    
     return tile_grid_str




if __name__ == "__main__":
    p = P.Params()
    p.init(__doc__)  ## Put description of the code here
    logger = util.get_logger(p)
    main()
