#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumotable import *

def PrintRikishi(rinput):
    # print(rinput)
    if hasattr(rinput, '__len__'):
        for r in rinput:
            print(r)
    else:
        print(rinput)

def TestTable():
    sumotable = None
    try:
        sumotable = SumoTable.load_table('./basho_202405.pickle')
    except:
        pass

    if not sumotable:
        sumotable = SumoTable()
    sumotable.print_table_stats()

    sumotable.build_table_from_dates(date(2024,4,23), date(2024,6,21))
    # sumotable.build_table_from_dates(date(2024,4,23), date(2024,6,21), SumoDivision.Makuuchi)
    sumotable.save_table('./sumo_data.pickle')
    sumotable.print_table_stats()

    # get Hokutofuji (id=27) record in the basho that should be in the table now
    hokutofuji = sumotable.get_rikishi(27)
    if hokutofuji:
        record, division = sumotable.get_rikishi_basho_record(hokutofuji.id(), '202405')
        print(f'\n{hokutofuji}: {division}\nRecord: {record}\n')
    else:
        print('Where is Hokutofuji?!')

    ichiyamamoto = sumotable.get_rikishi(11)
    if ichiyamamoto:
        matchup = sumotable.get_matchup_record(hokutofuji.id(), ichiyamamoto.id())
        print(f'\n{hokutofuji} vs {ichiyamamoto}:\n{matchup}\n')
    else:
        print('Where is Ichiyamamoto?!')

    ura = sumotable.find_rikishi('Ura')
    if ura:
        print(f'\nLOOKUP: {ura}\n')
    else:
        print('Where is Ura?!')

    return sumotable

def BuildBigTable(sumotable):
    startDate = date(2000,1,1)
    endDate = date(2024,12,31)

    curDate = startDate

    sumotable = SumoTable()

    # run through the date range in year increments and save after each year
    while curDate < endDate:
        bStart = curDate
        bEnd = curDate + relativedelta(years=1)
        sumotable.build_table_from_dates(bStart, bEnd)
        # create new files after each year just to see the progress
        fname = f'sumodata_{BashoIdStr(startDate)}_{BashoIdStr(bEnd)}.pickle'
        print(f'Saving Data in {fname}')
        sumotable.save_table(fname)
        curDate = bEnd + relativedelta(months=1)

    return

t = TestTable()
BuildBigTable(t)
