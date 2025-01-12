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

    # sumotable.build_table_from_dates(date(2024,4,23), date(2024,6,21))
    sumotable.build_table_from_dates(date(2024,4,23), date(2024,6,21), SumoDivision.Makuuchi)
    sumotable.save_table('./sumo_data.pickle')
    sumotable.print_table_stats()

    # get Hokutofuji (id=27) record in the basho that should be in the table now
    hokutofuji = sumotable.get_rikishi(27)
    record, division = sumotable.get_rikishi_basho_record(hokutofuji.id(), '202405')
    print(f'\n{str(hokutofuji)}: {division}\nRecord: {record}\n')

    ichiyamamoto = sumotable.get_rikishi(11)
    matchup = sumotable.get_matchup_record(hokutofuji.id(), ichiyamamoto.id())
    print(f'\n{str(hokutofuji)} vs {str(ichiyamamoto)}:\n{matchup}\n')

    return

TestTable()
