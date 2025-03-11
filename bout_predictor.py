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

import argparse

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
    if not boutlist:
        return bout_info
    for bout in boutlist:
        binfo = BoutInfo(bout)

        if bout.winnerId > 0:
            binfo.winner = sumodata.get_rikishi(bout.winnerId)

        eastMatchup = sumodata.get_matchup(bout.eastId, bout.westId)

        # Run the prediction!
        if DEBUG:
            east = sumodata.get_rikishi(bout.eastId)
            west = sumodata.get_rikishi(bout.westId)
            sys.stdout.write(f'{east} vs. {west}\n')
        projectedWinner, confidence = predictor.predict(eastMatchup, basho, division, day, DEBUG=DEBUG)

        binfo.projectedWinner = projectedWinner
        binfo.projectionConfidence = confidence
        if DEBUG:
            sys.stdout.write(f'  ProjectedWinner: {projectedWinner} ({confidence})\n')
            sys.stdout.write(f'  ActualWinner: {binfo.winner}\n')

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

def PredictAndPrintBasho(args, sumodata, predictor, basho, division, day = -1):
    bout_info_on_day:dict[int, list[BoutInfo]] = {}

    banzuke = basho.get_banzuke(division)

    start_day = 0
    end_day = 0
    num_days = 0
    if day > 0:
        num_days = 1
        start_day = day
        end_day = day + 1
        boutlist = basho.get_bouts_in_division_on_day(division, day)
        bout_info_on_day[day] = GetProjectedWinners(sumodata, predictor, basho, division, day, boutlist, \
                                                    DEBUG=args.debug_prediction)
    else:
        num_days = basho.num_days()
        start_day = 1
        end_day = start_day + num_days
        for day in range(1, num_days+1):
            boutlist = basho.get_bouts_in_division_on_day(division, day)
            bout_info_on_day[day] = GetProjectedWinners(sumodata, predictor, basho, division, day, boutlist, \
                                                    DEBUG=args.debug_prediction)

    correctPredictions = 0
    totalPredictions = 0

    # Print it all out
    for day in range(start_day, end_day):
        if args.verbose > 0:
            print(f'\n{"*"*79}\nBasho {basho.id_str()}, Day {day}, {division}')
        for bout in bout_info_on_day[day]:
            _rday = day - 1
            if day <= 1:
                _rday = 0
            east = sumodata.get_rikishi(bout.match.eastId)
            eastRecord = banzuke.get_record_on_day(east.id(), _rday)
            west = sumodata.get_rikishi(bout.match.westId)
            westRecord = banzuke.get_record_on_day(west.id(), _rday)

            if args.verbose > 0:
                if args.verbose > 1:
                    PrintBoutInfo(sumodata, bout.match, east.id(), eastRecord, west.id(), westRecord)
                else:
                    sys.stdout.write(f'\nMatch {bout.match.matchNo}\n')
                    sys.stdout.write(f'    {east} vs. {west}\n')

            # After the bout info, print out the projected winner and actual winner
            if args.verbose > 0:
                sys.stdout.write(f'        Projected Winner: {bout.projectedWinner}, Confidence:{abs(bout.projectionConfidence):.2%}\n')
            if bout.winner:
                if args.verbose > 0:
                    sys.stdout.write(f'        Actual Winner: {bout.winner}\n')
                if bout.projectedWinner.id() == bout.winner.id():
                    correctPredictions += 1
            totalPredictions += 1

    if args.verbose > 0:
        sys.stdout.write('\n\n')

    pct = 0.0
    if totalPredictions > 0:
        pct = float(correctPredictions) / float(totalPredictions)
    print(f'Total Predictions: {totalPredictions}')
    print(f'Correct Predictions: {correctPredictions} ({pct:.2%})')


########################################################################
#
# Main
#
########################################################################
if not __name__ == '__main__':
    sys.exit(0)

#
# Setup argument parsing
#

parser = argparse.ArgumentParser()

parser.add_argument('-b', '--basho', dest='basho', type=str, metavar='YYYYMM', nargs='+', \
                    action='extend', required=True, \
                    help='Basho to predict. Format is YYYYMM, e.g., 202501. This argument can be repeated to predict multiple basho')
parser.add_argument('-d', '--division', dest='division', type=str, metavar='DIVISION', \
                    default='Makuuchi', \
                    choices=list(map(lambda d: str(d.value), (SumoDivision))), \
                    help='Sumo division in Basho to predict.')
parser.add_argument('--day', dest='day', type=int, metavar='DAY', \
                    required=False, help='Only consider bouts on the given day.')

parser.add_argument('--force_fetch', action='store_true', \
                    help='Force fetching of basho data from SumoAPI service')
parser.add_argument('--db', type=str, metavar='<DATA_FILE>', \
                    default='sumo_data.pickle', \
                    help='All data from the SumoAPI server will be cached in this file.')
parser.add_argument('-v', '--verbose', dest='verbose', action='count', \
                    default=0, \
                    help='Increase verbosity of output (specify multiple times to increase verbosity)')

parser.add_argument('--debug_prediction', action='store_true', \
                    help='Turn on prediction debuging')
parser.add_argument('--debug_api', action='store_true', \
                    help='Turn on API debuging')

args = parser.parse_args()

# debug and verbose flags get passed to class-level values so we can easily
# enable API debugging if we want
if args.debug_api:
    SumoAPI._DEBUG=True
if args.verbose > 2:
    SumoAPI._VERBOSE=args.verbose - 2

# Load any saved data
sumodata = None
try:
    # save data to avoid lots of API queries
    sumodata = SumoData.load_data(args.db)
except:
    sumodata = SumoData()

# Create an empty prediction instance 
#
predictor = SumoBoutPredictor(sumodata)

#
# Create a list of comparison objects.
# When constructing each, you can give a weight to that comparison.
#
#comparisons:list[SumoBoutCompare] = [ \
#    CompareBMI(sumodata, 1.05), \
#    CompareHeight(sumodata, 2.72), \
#    CompareWeight(sumodata, 1.71), \
#    CompareAge(sumodata, 2.66), \
#    CompareRank(sumodata, 8.79), \
#    CompareBashoRecord(sumodata, 51.35), \
#    CompareHeadToHeadFull(sumodata, 10.55), \
#    CompareHeadToHeadCurrentDivision(sumodata, 10.68), \
#    CompareOverallRecord(sumodata, 10.49)
#]
comparisons:list[SumoBoutCompare] = [ \
    CompareBMI(sumodata, 1.78), \
    CompareHeight(sumodata, 4.64), \
    CompareWeight(sumodata, 2.91), \
    CompareAge(sumodata, 4.53), \
    CompareRank(sumodata, 14.97), \
    CompareBashoRecord(sumodata, 17.16), \
    CompareHeadToHeadFull(sumodata, 17.96), \
    CompareHeadToHeadCurrentDivision(sumodata, 18.18), \
    CompareOverallRecord(sumodata, 17.86) \
]
predictor.add_comparisons(comparisons)

# set the division to focus on from the input arguments
division = SumoDivision(args.division)

# load the basho data and fetch the latest info from the server
basho_list = []
for b in args.basho:
    if args.verbose > 0:
        sys.stdout.write(f'Loading basho {b}...\n')
    _basho =sumodata.get_basho(b, [division], fetch=args.force_fetch)
    if not _basho:
        _basho = sumodata.get_basho(b, [division], fetch=True)
    if _basho:
        basho_list.append(_basho)

# save the data we just fetched
sumodata.save_data(args.db)
if args.verbose > 0:
    sumodata.print_table_stats()


on_day = -1
if args.day:
    on_day = args.day

for basho in basho_list:
    PredictAndPrintBasho(args, sumodata, predictor, basho, division, day=on_day)

