#!/usr/bin/env python3
#
# learn_prediction_weights.py
#
# 
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
from predictor_loader import *


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
parser.add_argument('--load-config', dest='load_config', type=str, metavar='<FILE>', \
                    help='Specify the config file used to construct a sumo bout predictor object')
parser.add_argument('--save-config', dest='save_config', type=str, metavar='<FILE>', \
                    help='Save suggested configuration to <FILE>')
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

#
# Create a predictor instance based on a config file, or default to a fixed set of comarators and weights
#
predictor = None
if args.load_config:
    predictor = SumoBoutPredictorLoader.from_json(args.load_config, sumodata)
    if not predictor:
        sys.stderr.write(f'Could not create predictor from config file "{args.load_config}"\n')
        sys.exit(-1)
else:
    predictor = SumoBoutPredictor(sumodata)
    #
    # Create a list of comparison objects.
    # When constructing each, you can give a weight to that comparison.
    #
    comparisons:list[SumoBoutCompare] = [ \
        CompareBMI(sumodata, 1.46), \
        CompareHeight(sumodata, 3.28), \
        CompareWeight(sumodata, 2.24), \
        CompareAge(sumodata, 5.24), \
        CompareRank(sumodata, 15.08), \
        CompareBashoRecord(sumodata, 15.50), \
        CompareHeadToHeadFull(sumodata, 15.13), \
        CompareHeadToHeadCurrentDivision(sumodata, 15.18), \
        CompareOverallRecord(sumodata, 15.16), \
        CompareWinStreak(sumodata, 11.74) \
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


if args.verbose > 0:
    ch = predictor.get_comp_history()
    if ch:
        total = 0.0
        for k,v in ch.items():
            sys.stdout.write(f'{k} = {str(v)}\n')
            dist = v.pct_correct() - 0.50
            total += v.distance_from_p50()
        for k,v in ch.items():
            pct = v.distance_from_p50() / total
            sys.stdout.write(f'{k}:{pct:.2%}\n')

jstr = SumoBoutPredictorLoader.to_json(predictor)
if args.verbose > 0:
    sys.stdout.write(jstr)
    sys.stdout.write('\n\n')

if args.save_config:
    SumoBoutPredictorLoader.save_json(predictor, args.save_config)

sys.stdout.write("Stats: { ")
for k,v in prediction_stats.items():
    sys.stdout.write(f'{k}:{v:.2f} ')
sys.stdout.write("}\n")

win_pct = prediction_stats['win_num'] / (prediction_stats['win_num'] + prediction_stats['lose_num'])
sys.stdout.write(f'Win Pct: {win_pct:.2%}\n')
