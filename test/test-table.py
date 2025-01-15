#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumodata import *

def PrintRikishi(rinput):
    # print(rinput)
    if hasattr(rinput, '__len__'):
        for r in rinput:
            print(r)
    else:
        print(rinput)

def TestTable():
    sumodata = None
    try:
        sumodata = SumoData.load_data('./basho_202405.pickle')
    except:
        pass

    if not sumodata:
        sumodata = SumoData()
    sumodata.print_table_stats()

    sumodata.add_basho_by_date_range(date(2024,4,23), date(2024,6,21))
    # sumodata.add_basho_by_date_range(date(2024,4,23), date(2024,6,21), SumoDivision.Makuuchi)
    sumodata.save_data('./sumo_data.pickle')
    sumodata.print_table_stats()

    # get Hokutofuji (id=27) record in the basho that should be in the table now
    hokutofuji = sumodata.get_rikishi(27)
    if hokutofuji:
        record, division = sumodata.get_rikishi_basho_record(hokutofuji.id(), '202405')
        print(f'\n{hokutofuji}: {division}\nRecord: {record}\n')
    else:
        print('Where is Hokutofuji?!')

    ichiyamamoto = sumodata.get_rikishi(11)
    if ichiyamamoto:
        matchup = sumodata.get_matchup_record(hokutofuji.id(), ichiyamamoto.id())
        print(f'\n{hokutofuji} vs {ichiyamamoto}:\n{matchup}\n')
    else:
        print('Where is Ichiyamamoto?!')

    ura = sumodata.find_rikishi('Ura')
    if ura:
        print(f'\nLOOKUP: {ura}\n')
    else:
        print('Where is Ura?!')

    return sumodata

def BuildBigTable(sumodata = None, preload_file = './sumodata_200001_201212.pickle'):
    startDate = date(2000,1,1)
    endDate = date(2024,12,31)

    curDate = date(2013,1,1) # startDate

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

# t = TestTable()
# BuildBigTable(t)
BuildBigTable()
