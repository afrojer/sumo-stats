#!/usr/bin/env python3

import argparse
import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumodata import *
from sumostats.sumoclasses import __EMPTY_BASHO_DATE__


########################################################################
#
# Main
#
########################################################################
if not __name__ == '__main__':
    sys.exit(0)

#
# Setup argument parsing
#

parser = argparse.ArgumentParser()

parser.add_argument('--start', dest='start_date', type=str, metavar='YYYYMM', \
                    action='store', required=True, \
                    help='Basho (month) from which to start building the database.')
parser.add_argument('--end', dest='end_date', type=str, metavar='YYYYMM', \
                    action='store', required=True, \
                    help='Basho (month) on which to end the database.')
parser.add_argument('-d', '--division', dest='division', type=str, nargs='+', \
                    metavar='DIVISION', action='extend', \
                    choices=list(map(lambda d: str(d.value), (SumoDivision))), \
                    help='Restrict data downloaded to this (set of) division(s)')

parser.add_argument('--db', dest='dbfile', type=str, metavar='FILE', \
                    action='store', default='sumo_data.pickle', \
                    help='Save (and load) sumo db from this file.')

parser.add_argument('-v', '--verbose', dest='verbose', action='count', \
                    default=0, \
                    help='Increase verbosity of output')
parser.add_argument('--debug_api', action='store_true', \
                    help='Turn on API debuging')

args = parser.parse_args()

# debug and verbose flags get passed to class-level values so we can easily
# enable API debugging if we want
if args.debug_api:
    SumoAPI._DEBUG=True
if args.verbose > 1:
    SumoData._VERBOSE = args.verbose - 1
if args.verbose > 2:
    SumoAPI._VERBOSE=args.verbose - 2

# parse divisions from arguments
divisions = []
if args.division:
    for d in args.division:
        divisions.append(SumoDivision(d))

#
# Load any saved data
#
sumodata = None
try:
    print(f'Loading db from {args.dbfile}...')
    sumodata = SumoData.load_data(args.dbfile)
except OSError as e:
    # something went wrong opening the file.
    # create a new empty object and try to write the file to make sure
    # the path os accessible
    print(f'Creating empty db in {args.dbfile}...')
    sumodata = SumoData()
    # this will re-throw if something goes wrong
    sumodata.save_data(args.dbfile)

if not sumodata:
    sys.stderr.write(f'ERROR loading sumo data from {args.dbfile}\n')
    sys.exit(-1)

if args.verbose > 0:
    sumodata.print_table_stats()
print('')

# parse start and end dates from arguments
startDate = BashoDate(sumodata.find_next_basho(BashoDate(args.start_date)))
endDate = BashoDate(args.end_date)
if startDate == __EMPTY_BASHO_DATE__:
    sys.stderr.write(f'')
    sys.exit(-1)

# run through the date range in year increments and save after each year
curDate = startDate
while curDate < endDate:
        bStart = curDate
        bEnd = curDate + relativedelta(years=1)
        if bEnd > endDate:
            bEnd = endDate

        # This function will only fetch data when it needs to
        sumodata.add_basho_by_date_range(bStart, bEnd, divisions)
        if args.verbose > 1:
            sys.stdout.write(f'{startDate} - {bEnd}: ')
            sumodata.print_table_stats()
        sumodata.save_data(args.dbfile)
        curDate = bEnd + relativedelta(months=1)

print(f'Sumo Data ready in {args.dbfile}')
sumodata.print_table_stats()
