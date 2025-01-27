#!/usr/bin/env python3
#
# bout_predictor.py
#
# An example script which attempts to find a set of matchups, and
# then use a fixed list of comparators to predict the outcome.
#

import os
import sys
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)

from sumostats.sumodata import *
from sumostats.sumocalc import *

from compare_physical import *
from compare_record import *

sumodata = None
try:
    # save data to avoid lots of API queries
    sumodata = SumoData.load_data('./sumo_data.pickle')
except:
    sumodata = SumoData()

# load the 2025-01 basho data and fetch the latest info from the server
basho = sumodata.get_basho('202501', SumoDivision.Makuuchi) #, fetch=True)
if not basho:
    basho = sumodata.get_basho('202501', SumoDivision.Makuuchi, fetch=True)
banzuke = basho.get_banzuke(SumoDivision.Makuuchi)

# save the data we just fetched
sumodata.save_data('./sumo_data.pickle')
#sumodata.print_table_stats()

#
# Create an empty prediction instance 
#
predictor = SumoBoutPredictor(sumodata)

#
# Create a list of comparison objects.
# When constructing each, you can give a weight to that comparison.
#
physical_comparison:list[SumoBoutCompare] = [ \
    CompareBMI(sumodata, 0.3), \
    CompareHeight(sumodata, 0.2), \
    CompareWeight(sumodata, 0.2), \
    CompareRank(sumodata, 1.5), \
    CompareBashoRecord(sumodata, 1.8), \
    CompareHeadToHeadFull(sumodata, 0.8), \
    CompareHeadToHeadCurrentDivision(sumodata, 1.7), \
    CompareOverallRecord(sumodata, 1.2)
]
predictor.add_comparisons(physical_comparison)



# get a list of upcoming bouts (the first day where no bout has a listed winner)
# boutlist is a list of BashoMatch objects
day = 0
boutlist = []
# day, boutlist = basho.get_upcoming_bouts(SumoDivision.Makuuchi)

# If there wasn't a list of upcoming bouts, then grab a random day and print it out
if len(boutlist) == 0:
    day = 9
    boutlist = basho.get_bouts_in_division_on_day(SumoDivision.Makuuchi, day)

print(f'\nBasho {basho.id_str()}, Day {day}')

for bout in boutlist:
    sys.stdout.write(f'{"-"*78}\nMatch: {bout.matchNo}\n')

    east = sumodata.get_rikishi(bout.eastId)
    eastRecord = banzuke.get_record_on_day(east.id(), day)

    west = sumodata.get_rikishi(bout.westId)
    westRecord = banzuke.get_record_on_day(west.id(), day)

    #
    # Generate the matchup record for these two, use the "east" side as the
    # Rikishi in the matchup object. So it's "east" vs. "west" (opponent)
    #
    eastMatchup = sumodata.get_matchup(east.id(), west.id())

    # Run the prediction!
    projectedWinner, confidence = predictor.predict(eastMatchup, basho, SumoDivision.Makuuchi, day, DEBUG=False)

    #
    # Print Stats
    #
    eastDescription = f'{east.shikonaEn()} ({east.rikishi.currentRank})'
    westDescription = f'{west.shikonaEn()} ({west.rikishi.currentRank})'
    sys.stdout.write(f'{eastDescription:>35}  -vs-  {westDescription:<35}\n')

    # record in the bazuke/basho
    if eastRecord:
        desc = f'{eastRecord.wins}-{eastRecord.losses}'
        if eastRecord.absences > 0:
            desc += f'-{eastRecord.absences}'
        sys.stdout.write(desc.center(35))
    else:
        sys.stdout.write(f'{" "*35}')
    sys.stdout.write(f'{" "*8}')
    if westRecord:
        desc = f'{westRecord.wins}-{westRecord.losses}'
        if westRecord.absences > 0:
            desc += f'-{westRecord.absences}'
        sys.stdout.write(desc.center(35))
    else:
        sys.stdout.write(f'{" "*35}')

    # Matchup History
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

    # Finall the good stuff: print the prediced winner!
    sys.stdout.write(f'\nProjected Winner: {projectedWinner}, Confidence:{abs(confidence):.2%}')

    if bout.winnerId > 0:
        actualWinner = sumodata.get_rikishi(bout.winnerId)
        sys.stdout.write(f'\nActual Winner: {actualWinner}')

    sys.stdout.write('\n\n')
