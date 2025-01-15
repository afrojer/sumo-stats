#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumodata import *

def TestBasicDataAPIs():
    sumodata = None
    try:
        sumodata = SumoData.load_data('./sumo_data.pickle')
    except:
        pass

    if not sumodata:
        sumodata = SumoData()
    sumodata.print_table_stats()

    # Try to build a rankValue table from all the rikshi in a basho
    basholist = []
    basholist.append(sumodata.get_basho('202405', fetch=True))
    basholist.append(sumodata.get_basho('202411', fetch=True))
    basholist.append(sumodata.get_basho('202501', fetch=True))
    sumodata.save_data('./sumo_data.pickle')
    sumodata.print_table_stats()

    rankMap: dict[str, int] = {}
    def updateranks(basho):
        for r in basho.rikishi:
            w = sumodata.get_rikishi(r)
            history = w.get_rank_history()
            for rank in history:
                if rank.rankValue > 0 and not rank.rank in rankMap:
                    rankMap[rank.rank] = rank.rankValue

    for basho in basholist:
        updateranks(basho)

    print('Sorting Sumo Ranks...')
    for r in dict(sorted(rankMap.items(), key=lambda item: item[1])).items():
        print(f'    "{r[0]}": {r[1]}')

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

t = TestBasicDataAPIs()
# BuildBigTable(t)
#BuildBigTable()
