#!/usr/bin/env python3
#
# list_matchups.py
#
# An example script which attempts to find a set of bouts in a day
# and prints out information about each bout's matchup
#

import os
import sys
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)

from sumostats.sumodata import *

sumodata = None
try:
    # save data to avoid lots of API queries
    sumodata = SumoData.load_data('./sumo_data.pickle')
except:
    sumodata = SumoData()

# load the 2025-01 basho data and fetch the latest info from the server
basho = sumodata.get_basho('202503', [SumoDivision.Makuuchi], fetch=True)

# save the data we just fetched
sumodata.save_data('./sumo_data.pickle')
#sumodata.print_table_stats()

# get a list of upcoming bouts (the first day where no bout has a listed winner)
day, boutlist = basho.get_upcoming_bouts(SumoDivision.Makuuchi)

# If there wasn't a list of upcoming bouts, then grab a random day and print it out
if len(boutlist) == 0:
    day = 1
    boutlist = basho.get_bouts_in_division_on_day(SumoDivision.Makuuchi, day)

print(f'\nBasho {basho.id_str()}, Day {day}')
if not boutlist:
    sys.stderr.write(f'No bouts found!\n')
    sys.exit(0)

for bout in boutlist:
    sys.stdout.write(f'{"-"*78}\nMatch: {bout.matchNo}\n')

    east = sumodata.get_rikishi(bout.eastId)
    west = sumodata.get_rikishi(bout.westId)

    eastMatchup = sumodata.get_matchup(east.id(), west.id())
    # westMatchup = sumodata.get_matchup(west.id(), east.id())

    eastDescription = f'{east.shikonaEn()} ({east.rikishi.currentRank})'
    westDescription = f'{west.shikonaEn()} ({west.rikishi.currentRank})'
    sys.stdout.write(f'{eastDescription:>35}  -vs-  {westDescription:<35}\n')
    if not eastMatchup or eastMatchup.total_matches() == 0:
        sys.stdout.write(f'\nFirst meeting')
    else:
        # last 6 basho
        nbasho = 6
        for match in eastMatchup.each_match():
            win_kimarite = ''
            lose_kimarite = ''
            if match.winnerId== east.id():
                win_kimarite = match.kimarite
            else:
                lose_kimarite = match.kimarite
            sys.stdout.write(f'\n    {win_kimarite:>31} {BashoIdStr(match.bashoId)} {lose_kimarite:<35}')
            nbasho -= 1
            if nbasho == 0:
                break

        # win[-fusensho] - loss[+fusenpai]
        sys.stdout.write(f'\n    {eastMatchup.wins(True)}')
        if eastMatchup.fusensho() > 0:
            sys.stdout.write(f'[-{eastMatchup.fusensho()}]')
        sys.stdout.write(f' - {eastMatchup.losses(True)}')
        if eastMatchup.fusenpai() > 0:
            sys.stdout.write(f'[+{eastMatchup.fusenpai()}]')

        # win-loss in each division
        for div, matchup in eastMatchup.each_division():
            sys.stdout.write(f'\n    {div:10}: {matchup.rikishiWins}-{matchup.opponentWins}')

    sys.stdout.write('\n\n')
