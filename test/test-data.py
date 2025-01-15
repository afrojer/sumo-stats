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

def TestBasicDataAPIs():
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


t = TestBasicDataAPIs()
