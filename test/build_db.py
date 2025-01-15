#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumodata import *

def BuildBigTable(sumodata = None, preload_file = './sumodata_200001_201212.pickle', curDate = date(2000,1,1)):
    startDate = date(2000,1,1)
    endDate = date(2024,11,30)

    if not sumodata:
        if os.path.isfile(preload_file):
            print(f'Loading data from {preload_file}...')
            try:
                sumodata = SumoData.load_data(preload_file)
            except:
                sumodata = SumoData()
                sys.stderr.write(f'Error loading data from {preload_file}...')
                pass
        else:
            sumodata = SumoData()

    sumodata.print_table_stats()

    # Try to load the 201103 basho b/c it's all goofed up
    print(f'Trying to update 201103...')
    sumodata.add_basho_by_date_range(date(2011,2,1), date(2011,4,1))
    sumodata.update_basho(date(2011,3,1))
    sumodata.print_table_stats()

    # run through the date range in year increments and save after each year
    while curDate < endDate:
        bStart = curDate
        bEnd = curDate + relativedelta(years=1)
        sumodata.add_basho_by_date_range(bStart, bEnd)
        sumodata.print_table_stats()
        # create new files after each year just to see the progress
        fname = f'sumodata_{BashoIdStr(startDate)}_{BashoIdStr(bEnd)}.pickle'
        print(f'Saving Data in {fname}')
        sumodata.save_data(fname)
        curDate = bEnd + relativedelta(months=1)

    return

BuildBigTable()
