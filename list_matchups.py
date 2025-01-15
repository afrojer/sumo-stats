#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)
from sumostats.sumodata import *

sumodata = None
try:
    sumodata = SumoData.load_data('./sumo_data.pickle')
except:
    sumodata = SumoData()

basho = sumodata.get_basho('202501', SumoDivision.Makuuchi, fetch=True)
sumodata.save_data('./sumo_data.pickle')
sumodata.print_table_stats()

day, boutlist = basho.get_upcoming_bouts(SumoDivision.Makuuchi)

print(f'Basho {basho.id()}, Day {day}')

for bout in boutlist:
    east = sumodata.get_rikishi(bout.eastId)
    west = sumodata.get_rikishi(bout.westId)
    eastMatchup = sumodata.get_matchup_record(east.id(), west.id())


    sys.stdout.write(f'{east.shikonaEn()} ({east.rikishi.currentRank}) vs {west.shikonaEn()} ({west.rikishi.currentRank}) | ')
    if eastMatchup:
        sys.stdout.write(f'{eastMatchup.rikishiWins}-{eastMatchup.opponentWins}')
    else:
        sys.stdout.write(f'first meeting')
    sys.stdout.write('\n')
