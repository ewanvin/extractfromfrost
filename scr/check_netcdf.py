#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checking CF-NetCDF files in a structure to ensure that all files have the same number of variables and allows aggregation in time.
"""
__author__ = "Øystein Godøy"
#__copyright__ = "Copyright Info"
__credits__ = ["Øystein Godøy",]
__license__ = """
    This file is part of extractfromfrost.

    This is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    This file is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with Foobar. If not, see <https://www.gnu.org/licenses/>. 
    """
__version__ = "0.0.0"
__maintainer__ = "Øystein Godøy"
__email__ = "steingod@met.no"
#__status__ = "status of the file"

import os
import sys
import argparse
import logging
import logging.handlers
from netCDF4 import Dataset
import numpy
import pytz
from datetime import datetime
import json

def parse_arguments():
    """
    Set up the command line interface.
    """
    parser = argparse.ArgumentParser(description="Checker for CF-NetCDF files to ensure consistency over files allowing aggregation in time.",epilog="")
    parser.add_argument("-d","--dest",dest="destination",
            help="Destination which to add NCML to", required=True)
    parser.add_argument("-l","--log",dest="logdir",
            help="Destination where to put logfiles", required=True)
    parser.add_argument("-o","--overwrite",action='store_true',
            help="Overwrite if NCML is existing")
    args = parser.parse_args()

    """
    if args.cfgfile is False:
        parser.print_help()
        parser.exit()
    """

    return args

def initialise_logger(outputfile = './log'):
    """
    Set up the logging for the application.
    """
    # Check that logfile exists
    logdir = os.path.dirname(outputfile)
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except:
            raise IOError
    # Set up logging
    mylog = logging.getLogger()
    mylog.setLevel(logging.INFO)
    #logging.basicConfig(level=logging.INFO, 
    #        format='%(asctime)s - %(levelname)s - %(message)s')
    myformat = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(myformat)
    mylog.addHandler(console_handler)
    file_handler = logging.handlers.TimedRotatingFileHandler(
            outputfile,
            when='w0',
            interval=1,
            backupCount=7)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(myformat)
    mylog.addHandler(file_handler)

    return(mylog)

def traverse_structure(myfolder):
    """
    Assuming data from one station is organised in a single folder and with sub folders for each year. This function loops through all stations.
    """

    for item in os.listdir(myfolder):
        mydir = '/'.join([myfolder,item])
        if not os.path.isdir(mydir):
            continue
        if not item.startswith('SN'):
            mylog.warn('Apparently this is not a station folder.')
            continue
        mylog.info('Processing folder: %s', mydir)
        try:
            check_netcdf(mydir)
        except Exception as e:
            mylog.error('Something failed.')
            raise

def compare_varlists(curlist, reflist):
    """
    Compare the content of 2 lists of variables.
    """
    curlist_sorted = sorted(curlist)
    reflist_sorted = sorted(reflist)
    if curlist_sorted != reflist_sorted:
        return(False)
    else:
        return(True)

def update_variables(ncds, missingvar):
    """
    Add missing variables to CF-NetCDF files. All values are set to missing.
    """

    if missingvar['dtype'] == 'int32':
        misval = ncds.createVariable(varname=missingvar['name'], datatype=missingvar['dtype'], dimensions='time', fill_value=int(missingvar['missing']))
    else:
        misval = ncds.createVariable(varname=missingvar['name'], datatype=missingvar['dtype'], dimensions='time', fill_value=float(missingvar['missing']))
    misval.standard_name = missingvar['stdname']
    misval.long_name = missingvar['lngname']
    misval.units = missingvar['units']
    if missingvar['dtype'] == 'int32':
        tmp = numpy.full(shape=ncds['time'].size, fill_value=missingvar['missing'], dtype=int)
        misval = tmp
    else:
        tmp = numpy.full(shape=ncds['time'].size, fill_value=missingvar['missing'], dtype=float)
        misval = tmp

    return

def update_vertlev(ncds, vertcoord, vertvalues):
    """
    Check vertical levels and make these consistent across files.
    """

    # List variables that typically are presented as profiles
    myvars = ['soil_temperature']
    mylog.info('Now in update_vertlev')

    myvertvalues = ncds[vertcoord][:]
    mydata = dict()
    mytimedim = ncds['time'].size
    print('mytimedim ', mytimedim)
    print('myvertvalues ',myvertvalues)
    print('vertvalues ',vertvalues)
    """
    mytimevalues = ncds['time'][:]
    print(mytimevalues)
    """
    for el in myvars:
        print(el)
        tmparr = ncds[el][:]
        # Create temporary array
        #mydata[el] = numpy.full(shape=(mytimedim,len(vertvalues)), fill_value=ncds[el]._FillValue, dtype=float)
        tmparr2 = numpy.full(shape=(mytimedim,len(vertvalues)), fill_value=ncds[el]._FillValue, dtype=float)
        # Fill temporary array
        for i in range(0,mytimedim):
            for j in range(0,len(vertvalues)):
                print(i, j)
                #print(vertvalues[j])
                #print(myvertvalues.index(j))
                #tmparr2[i,j] = tmparr[i,numpy.where(numpy.isclose(myvertvalues,[j]))[0]]
                myindex = numpy.where(numpy.isclose(myvertvalues,[vertvalues[j]]))
                print('>>> ', j, vertvalues[j])
                print('>>> ', myindex[0])
                print('>>> ', len(myindex[0]))
                if len(myindex[0]) != 0:
                    print('>>> ', vertvalues[j], myindex[0][0],tmparr[i][myindex[0][0]]) 
                    tmparr2[i][j] = tmparr[i][myindex[0][0]]
        mydata[el] = tmparr2

    print(tmparr2)
    print(mydata)

    """
    print(type(myvertvalues))
    print(myvertvalues.ndim)
    print(myvertvalues[0])
    mydata = ncds['soil_temperature'].dimensions)
    print(numpy.ma.getmask(myvertvalues))
    print(type(numpy.ma.getdata(myvertvalues)))
    print((numpy.ma.getdata(myvertvalues)))
    """

    sys.exit()

    return

def check_netcdf(stdir):
    """
    Check the individual files in the folder for each station. If some files miss variables that have been added later, these are added to the respective files and set to all missing values. This function works backwards under the assumption that there is a larger probability for variables to be added than removed.

    If featureTyppe is timeSeries it is assumed that all variables only have 1 dimension (time).
    If featureType is timeSeeriesProfile it is assumed that variables have 2 dimensions (time and depth). Depth can be in different units.
    """

    # vertical coordinates used...
    myvertcoord = ['depth','height']
    # Loop through folder
    missingvars = list()
    myvariables = dict()
    myzsize = None
    myvertvalues = list()
    for item in sorted(os.listdir(stdir), reverse=True):
        # Check content of yearly folder
        curdir = '/'.join([stdir,item])
        if os.path.isdir(curdir):
            # Process files for each year and extract list of variables
            for item2 in sorted(os.listdir(curdir), reverse=True):
                myfile = '/'.join([curdir,item2])
                # Only process NetCDF files and check content
                if myfile.endswith('.nc'):
                    mylog.info('Processing file: %s', myfile)
                    myncds = Dataset(myfile, 'r+')
                    tmpvars = list(myncds.variables.keys())
                    # TODO fix this!!
                    try:
                        featureType = myncds.getncattr('featureType')
                    except Exception as e:
                        mylog.error('This file does not have featureType.')
                        raise(e)
                    if featureType == 'timeSeriesProfile':
                        if 'soil_temperature' in tmpvars:
                            mydim = myncds['soil_temperature'].dimensions
                            if len(mydim) > 2:
                                mylog.error('Cannot handle more than 2 dimensions.')
                                raise
                            for i in mydim:
                                print(i)
                                if i in myvertcoord:
                                    myvert = i
                        if not myzsize:
                            myzsize = myncds[myvert].size
                            myvertvalues = myncds[myvert][:]
                        else:
                            if myncds[myvert].size != myzsize:
                                print(myvertvalues)
                                print(myncds[myvert][:])
                                mylog.warning('This sequence of tiles have varying vertical levels preventing aggregation in time.\n%d\n%d', myncds[myvert].size, myzsize)
                                try:
                                    update_vertlev(myncds, myvert, myvertvalues)
                                except Exception as e:
                                    raise Exception('This sequence of tiles have varying vertical levels preventing aggregation in time.')
                        print(myvert, myzsize)
                    if len(list(myvariables.keys())) == 0:
                        for el in tmpvars:
                            tmpdict = dict()
                            tmpdict['name'] = el 
                            tmpdict['stdname'] = myncds[el].getncattr('standard_name') 
                            tmpdict['lngname'] = myncds[el].getncattr('long_name')
                            tmpdict['units'] = myncds[el].getncattr('units')
                            tmpdict['dtype'] = str(myncds[el].dtype)
                            if el != 'time':
                                tmpdict['missing'] = str(myncds[el]._FillValue)
                            else:
                                tmpdict['missing'] = ""
                            myvariables[el] = tmpdict
                            """
                            print(json.dumps(myvariables, indent=2))
                            print(len(myvariables.keys()))
                            """
                        continue
                    """
                    print('#### ',myvariables, len(myvariables))
                    print('#### ',tmpvars, len(tmpvars))
                    print('#### ', compare_varlists(tmpvars, myvariables))
                    if len(tmpvars) != len(myvariables):
                        sys.exit()
                    """
                    if compare_varlists(tmpvars, list(myvariables.keys())) == False:
                        mylog.warning('This file has different variables than others\nReference: %s (%d)\nFile: %s (%d)',list(myvariables.keys()),len(list(myvariables.keys())), tmpvars, len(tmpvars))
                        for el in list(myvariables.keys()):
                            # If variable is missing add it...
                            if el not in tmpvars:
                                try:
                                    update_variables(myncds, myvariables[el])
                                except Exception as e:
                                    mylog.error('Something failed when updating file.')
                    else:
                        mylog.info('This file has the same variables as other files, continuing.')
                    myncds.close()
        #print('lats\n#### ', missingvars)

if __name__ == '__main__':
    
    # Parse command line arguments
    try:
        args = parse_arguments()
    except:
        raise SystemExit('Command line arguments didn\'t parse correctly.')

    # Parse configuration file
    #cfgstr = parse_cfg(args.cfgfile)

    # Initialise logging
    #output_dir = cfgstr['output']
    mylog = initialise_logger(args.logdir)
    mylog.info('Starting new check of CF-NetCDF files consistency...')

    try:
        traverse_structure(args.destination)
    except Exception as e:
        mylog.error('Something failed %s', e)
