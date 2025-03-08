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


#@dataclass()
#class BoutInfo():
#    match:BashoMatch
#    winner:SumoWrestler = None
#    projectedWinner:SumoWrestler = None
#    projectionConfidence:float = 0.0
#

def LearnProjectedWinners(sumodata, predictor, basho, division, day, boutlist, prediction_stats, DEBUG=False) -> None:
    for bout in boutlist:
        winnerId = 0
        if not bout.winnerId > 0:
            # skip matches that don't have winners
            sys.stderr.write(f'skipping match with no winner: {bout}\n')
            continue
        else:
            winnerId = bout.winnerId

        eastMatchup = sumodata.get_matchup(bout.eastId, bout.westId)

        # Run the prediction!
        #if DEBUG:
        #    east = sumodata.get_rikishi(bout.eastId)
        #    west = sumodata.get_rikishi(bout.westId)
        #    sys.stdout.write(f'{east} vs. {west}\n')
        predictor.learn_result(winnerId, eastMatchup, basho, division, day, DEBUG=DEBUG)
        pwinner, pct = predictor.predict(eastMatchup, basho, division, day, DEBUG=DEBUG)
        if pwinner.id() == winnerId:
            prediction_stats['win_weight'] += abs(pct)
            prediction_stats['win_num'] += 1
        else:
            prediction_stats['lose_weight'] += abs(pct)
            prediction_stats['lose_num'] += 1

    return


def LearnAboutBasho(args, sumodata, predictor, basho, division, prediction_stats):
    sys.stdout.write(f' Learning basho results for {basho.id_str()}...\n')
    num_days = basho.num_days()
    for day in range(1, num_days+1):
        sys.stdout.write(f' Day {day}...    \r')
        boutlist = basho.get_bouts_in_division_on_day(division, day)
        LearnProjectedWinners(sumodata, predictor, \
                              basho, division, day, \
                              boutlist, prediction_stats, DEBUG=args.debug_prediction)
    sys.stdout.write('\n')


## def PrintBoutInfo(sumodata, basho_match, eastId, eastRecord, westId, westRecord):
##     bashoId = basho_match.bashoId
## 
##     #
##     # print header
##     #
##     sys.stdout.write(f'\n{"-"*79}\nMatch {basho_match.matchNo}\n')
## 
##     east = sumodata.get_rikishi(eastId)
##     west = sumodata.get_rikishi(westId)
## 
##     #
##     # Generate the matchup record for these two, use the "east" side as the
##     # Rikishi in the matchup object. So it's "east" vs. "west" (opponent)
##     #
##     eastMatchup = sumodata.get_matchup(east.id(), west.id())
## 
##     #
##     # Print Stats
##     #
##     eastDescription = f'{east.shikonaEn()} ({east.rikishi.currentRank})'
##     westDescription = f'{west.shikonaEn()} ({west.rikishi.currentRank})'
##     sys.stdout.write(f'{eastDescription:>35}  -vs-  {westDescription:<35}\n')
## 
##     # record in the bazuke/basho
##     if eastRecord:
##         desc = f'{eastRecord.wins}-{eastRecord.losses}'
##         if eastRecord.absences > 0:
##             desc += f'-{eastRecord.absences}'
##         sys.stdout.write(desc.center(35))
##     else:
##         sys.stdout.write(f'{" "*35}')
##     sys.stdout.write(f'{" "*8}')
##     if westRecord:
##         desc = f'{westRecord.wins}-{westRecord.losses}'
##         if westRecord.absences > 0:
##             desc += f'-{westRecord.absences}'
##         sys.stdout.write(desc.center(35))
##     else:
##         sys.stdout.write(f'{" "*35}')
## 
##     # Matchup History
##     if not eastMatchup or eastMatchup.total_matches(beforeBasho=bashoId) == 0:
##         sys.stdout.write(f'\n    First meeting')
##     else:
##         # last 6 basho (not including this one)
##         nbasho = 6
##         for match in eastMatchup.each_match(beforeBasho=bashoId):
##             win_kimarite = ''
##             lose_kimarite = ''
##             if match.winnerId== east.id():
##                 win_kimarite = match.kimarite
##             else:
##                 lose_kimarite = match.kimarite
##             sys.stdout.write(f'\n    {win_kimarite:>31} {BashoIdStr(match.bashoId)} {lose_kimarite:<35}')
##             nbasho -= 1
##             if nbasho == 0:
##                 break
## 
##         # win[-fusensho] - loss[+fusenpai]
##         sys.stdout.write(f'\n    Head-to-Head Record\n    -------------------')
##         sys.stdout.write(f'\n    Overall: {eastMatchup.wins(True)}')
##         fusen=eastMatchup.fusensho(beforeBasho=bashoId)
##         if fusen > 0:
##             sys.stdout.write(f'[-{fusen}]')
##         sys.stdout.write(f' - {eastMatchup.losses(no_fusenpai=True, beforeBasho=bashoId)}')
##         fusen=eastMatchup.fusenpai(beforeBasho=bashoId)
##         if fusen > 0:
##             sys.stdout.write(f'[+{fusen}]')
## 
##         # win-loss in each division
##         for div, matchup in eastMatchup.each_division():
##             sys.stdout.write(f'\n    {div:10}: {matchup.rikishiWins}-{matchup.opponentWins}')
## 
##     sys.stdout.write('\n\n')


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
                    help='Basho to predict. Format is YYYYMM, e.g., 202501. This argument can be repeated to predict multiple basho. Use "ALL" to iterate over all basho in the db.')
parser.add_argument('-d', '--division', dest='division', type=str, metavar='DIVISION', \
                    default='Makuuchi', \
                    choices=list(map(lambda d: str(d.value), (SumoDivision))), \
                    help='Sumo division in Basho to predict.')
parser.add_argument('--force_fetch', action='store_true', \
                    help='Force fetching of basho data from SumoAPI service')
parser.add_argument('--db', type=str, metavar='<DATA_FILE>', \
                    default='sumo_data.pickle', \
                    help='All data from the SumoAPI server will be cached in this file.')
parser.add_argument('-v', '--verbose', dest='verbose', action='count', \
                    default=0, \
                    help='Increase verbosity of output')

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
#    CompareBMI(sumodata, 0.1), \
#    CompareHeight(sumodata, 0.3), \
#    CompareWeight(sumodata, 0.2), \
#    CompareAge(sumodata, 0.3), \
#    CompareRank(sumodata, 0.8), \
#    CompareBashoRecord(sumodata, 1.7), \
#    CompareHeadToHeadFull(sumodata, 0.9), \
#    CompareHeadToHeadCurrentDivision(sumodata, 0.9), \
#    CompareOverallRecord(sumodata, 0.9) \
#]
comparisons:list[SumoBoutCompare] = [ \
    CompareBMI(sumodata, 1.05), \
    CompareHeight(sumodata, 2.72), \
    CompareWeight(sumodata, 1.71), \
    CompareAge(sumodata, 2.66), \
    CompareRank(sumodata, 8.79), \
    CompareBashoRecord(sumodata, 51.35), \
    CompareHeadToHeadFull(sumodata, 10.55), \
    CompareHeadToHeadCurrentDivision(sumodata, 10.68), \
    CompareOverallRecord(sumodata, 10.49) \
]
predictor.add_comparisons(comparisons)

# set the division to focus on from the input arguments
division = SumoDivision(args.division)

# load the basho data and fetch the latest info from the server
use_all = False
for b in args.basho:
    if b == 'ALL':
        use_all = True

prediction_stats = {'win_weight': 0.0, 'win_num':0.0, \
                    'lose_weight': 0.0, 'lose_num': 0.0 }
if use_all:
    for _basho in sumodata.each_basho():
        LearnAboutBasho(args, sumodata, predictor, _basho, division, prediction_stats)
else:
    for b in args.basho:
        if args.verbose > 0:
            sys.stdout.write(f'Loading basho {b}...\n')
        _basho =sumodata.get_basho(b, [division], fetch=args.force_fetch)
        if not _basho:
            _basho = sumodata.get_basho(b, [division], fetch=True)
        if _basho:
            LearnAboutBasho(args, sumodata, predictor, _basho, division, prediction_stats)


#predictor.print_learned_results()
ch = predictor.get_comp_history()
if ch:
    total = 0.0
    for k,v in ch.items():
        sys.stdout.write(f'{k} = {v}\n')
        dist = v['correct'] - 0.50
        v['dist'] = dist
        total += dist
    for k,v in ch.items():
        pct = v['dist'] / total
        sys.stdout.write(f'{k}:{pct:.2%}\n')

print(prediction_stats)
win_pct = prediction_stats['win_num'] / (prediction_stats['win_num'] + prediction_stats['lose_num'])
sys.stdout.write(f'Win Pct: {win_pct}\n')
