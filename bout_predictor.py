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

from dataclasses import dataclass

from sumostats.sumodata import *
from sumostats.sumocalc import *

# local sumo comparison functions!
from compare_physical import *
from compare_record import *


@dataclass()
class BoutInfo():
    match:BashoMatch
    winner:SumoWrestler = None
    projectedWinner:SumoWrestler = None
    projectionConfidence:float = 0.0


def GetProjectedWinners(sumodata, predictor, basho, division, day, boutlist, DEBUG=False) -> list[BoutInfo]:
    bout_info = []
    for bout in boutlist:
        binfo = BoutInfo(bout)

        if bout.winnerId > 0:
            binfo.winner = sumodata.get_rikishi(bout.winnerId)

        eastMatchup = sumodata.get_matchup(bout.eastId, bout.westId)

        # Run the prediction!
        projectedWinner, confidence = predictor.predict(eastMatchup, basho, division, day, DEBUG=DEBUG)

        binfo.projectedWinner = projectedWinner
        binfo.projectionConfidence = confidence

        bout_info.append(binfo)

    return bout_info


def PrintBoutInfo(sumodata, basho_match, eastId, eastRecord, westId, westRecord):
    bashoId = basho_match.bashoId

    #
    # print header
    #
    sys.stdout.write(f'\n{"-"*79}\nMatch {basho_match.matchNo}\n')

    east = sumodata.get_rikishi(eastId)
    west = sumodata.get_rikishi(westId)

    #
    # Generate the matchup record for these two, use the "east" side as the
    # Rikishi in the matchup object. So it's "east" vs. "west" (opponent)
    #
    eastMatchup = sumodata.get_matchup(east.id(), west.id())

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
    if not eastMatchup or eastMatchup.total_matches(beforeBasho=bashoId) == 0:
        sys.stdout.write(f'\n    First meeting')
    else:
        # last 6 basho (not including this one)
        nbasho = 6
        for match in eastMatchup.each_match(beforeBasho=bashoId):
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
        sys.stdout.write(f'\n    Head-to-Head Record\n    -------------------')
        sys.stdout.write(f'\n    Overall: {eastMatchup.wins(True)}')
        fusen=eastMatchup.fusensho(beforeBasho=bashoId)
        if fusen > 0:
            sys.stdout.write(f'[-{fusen}]')
        sys.stdout.write(f' - {eastMatchup.losses(no_fusenpai=True, beforeBasho=bashoId)}')
        fusen=eastMatchup.fusenpai(beforeBasho=bashoId)
        if fusen > 0:
            sys.stdout.write(f'[+{fusen}]')

        # win-loss in each division
        for div, matchup in eastMatchup.each_division():
            sys.stdout.write(f'\n    {div:10}: {matchup.rikishiWins}-{matchup.opponentWins}')

    sys.stdout.write('\n\n')

########################################################################
#
# Main
#
########################################################################

# Load data
sumodata = None
try:
    # save data to avoid lots of API queries
    sumodata = SumoData.load_data('./sumo_data.pickle')
except:
    sumodata = SumoData()

# Create an empty prediction instance 
#
predictor = SumoBoutPredictor(sumodata)

#
# Create a list of comparison objects.
# When constructing each, you can give a weight to that comparison.
#
comparisons:list[SumoBoutCompare] = [ \
    CompareBMI(sumodata, 0.3), \
    CompareHeight(sumodata, 0.2), \
    CompareWeight(sumodata, 0.2), \
    CompareAge(sumodata, 0.2), \
    CompareRank(sumodata, 1.3), \
    CompareBashoRecord(sumodata, 1.8), \
    CompareHeadToHeadFull(sumodata, 0.8), \
    CompareHeadToHeadCurrentDivision(sumodata, 1.7), \
    CompareOverallRecord(sumodata, 1.2)
]
predictor.add_comparisons(comparisons)


# load the 2025-01 basho data and fetch the latest info from the server
basho = sumodata.get_basho('202501', SumoDivision.Makuuchi)
if not basho:
    basho = sumodata.get_basho('202501', SumoDivision.Makuuchi, fetch=True)

# save the data we just fetched
sumodata.save_data('./sumo_data.pickle')
#sumodata.print_table_stats()


bout_info_on_day:dict[int, list[BoutInfo]] = {}

division = SumoDivision.Makuuchi
banzuke = basho.get_banzuke(division)

num_days = basho.num_days()
for day in range(1, num_days+1):
    boutlist = basho.get_bouts_in_division_on_day(division, day)
    bout_info_on_day[day] = GetProjectedWinners(sumodata, predictor, basho, division, day, boutlist, DEBUG=False)


correctPredictions = 0
totalPredictions = 0

# Print it all out
for day in range(1, num_days+1):
    print(f'\n{"*"*79}\nBasho {basho.id_str()}, Day {day}, {division}')
    for bout in bout_info_on_day[day]:
        east = sumodata.get_rikishi(bout.match.eastId)
        eastRecord = banzuke.get_record_on_day(east.id(), day)
        west = sumodata.get_rikishi(bout.match.westId)
        westRecord = banzuke.get_record_on_day(west.id(), day)

        sys.stdout.write(f'\nMatch {bout.match.matchNo}\n')
        sys.stdout.write(f'    {east} vs. {west}\n')
        # PrintBoutInfo(sumodata, bout.match, eastId, eastRecord, westId, westRecord)

        # After the bout info, print out the projected winner and actual winner
        sys.stdout.write(f'        Projected Winner: {bout.projectedWinner}, Confidence:{abs(bout.projectionConfidence):.2%}\n')
        if bout.winner:
            sys.stdout.write(f'        Actual Winner: {bout.winner}\n')
            if bout.projectedWinner.id() == bout.winner.id():
                correctPredictions += 1
        totalPredictions += 1

sys.stdout.write('\n\n')

pct = float(correctPredictions) / float(totalPredictions)
print(f'Total Predictions: {totalPredictions}')
print(f'Correct Predictions: {correctPredictions} ({pct:.2%})')

