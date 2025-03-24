#!/usr/bin/env python3

from .sumodata import *

import random
from datetime import date
from dateutil.relativedelta import *
import sys

##
## SumoBoutCompare
##
class SumoBoutCompare():
    """
    SumoBoutCompare

    Base class for generating a probability of the outcome of a bout. To create a comparator,
    derive a new class, and override the compare() method. In that method, you can use
    self._data as a SumoData object if you need additional context.

    """
    def __init__(self, data:SumoData, weight:float = 1.0, shift:float = 0.0):
        self._data = data
        self._weight = weight
        self._shift = shift
        self._DEBUG = False
        if not self._data:
            raise Exception('data cannot be empty/None')

    def compare(self, matchup:SumoMatchup, basho:SumoTournament, division:SumoDivision, day:int) -> float:
        """
        Override this method

        Return:
          [-1, 0) to favor opponent
          (0, 1] to favor rikishi
          [0] to pass-through with no opinion about this matchup
        """
        return 0.0

    def weight(self) -> float:
        return self._weight

    def shift(self) -> float:
        return self._shift

    def name(self) -> str:
        return type(self).__name__

    def debug(self, fmtStr, **kwargs):
        if not self._DEBUG:
            return
        # run through the arguments like this to avoid evaluating
        # all the format strings on calls to debug() when _DEBUG is not set
        for key, value in kwargs.items():
            fmtStr = fmtStr.replace(f'@{key}', repr(value))
        sys.stdout.write(f'  {self.name()}: {fmtStr}\n')

    def __call__(self, matchup:SumoMatchup, basho:SumoTournament, division:SumoDivision, day:int, DEBUG=False) -> float:
        # Call the comparison function
        self._DEBUG = DEBUG
        _pct = self.compare(matchup, basho, division, day)

        result = _pct
        _w = self._weight

        result = result * _w

        self._DEBUG = False
        return result, _w


##
## SumoBoutPredictor
##
class SumoBoutPredictor():
    """
    BoutPredictor

    This class holds a list of comparisons, each of which generate a probability of bout
    outcome. The predict() function takes a SumoMatchup object and returns a predicted
    Rikishi winner along with a confidence (float).

    """
    def __init__(self, data:SumoData, comparison:list[SumoBoutCompare] = []):
        self._data: SumoData = data
        self._comparison: list[SumoBoutCompare] = comparison
        self._comphistory: list[dict[str, float]] = []

    ##
    ## add_comparison
    ##
    def add_comparison(self, compare:SumoBoutCompare):
        """
        Add a single bout comparison object to the predictor
        """
        self._comparison.append(compare)
        return

    ##
    ## add_comparisons
    ##
    def add_comparisons(self, compare:list[SumoBoutCompare]):
        """
        Add a list of bout comparison objects to the predictor
        """
        self._comparison.extend(compare)
        return

    ##
    ## predict
    ##
    def predict(self, matchup:SumoMatchup, basho:SumoTournament, \
                division:SumoDivision, day:int, DEBUG=False) -> {SumoWrestler, float}:
        """
        Use all previously added bout comparison objects to predict the outcome
        of the specified matchup.

        This function will pass the matchup object to each comparison which will
        use the compare() function. Each comparison is weighted, and the final
        prediction is based on the sum of all the weights of all the comparison
        objects.
        """
        probability = 0.0
        if not len(self._comparison):
            if DEBUG:
                sys.stderr.write(f'No comparisons to make: randomly choosing\n')
            probability = 2.0*random.random() - 1.0
        else:
            weight = 0.0
            for c in self._comparison:
                _p, _w = c(matchup, basho, division, day, DEBUG)
                if DEBUG:
                    sys.stderr.write(f'  {c.name()}: _p={_p} w={_w}\n')
                probability += _p
                weight += _w
            if weight > 0.0:
                probability = probability / weight

        if probability >= 0.0:
            # favor the Rikishi in an even match (exactly 0.0)
            return matchup.rikishi, probability
        else:
            return matchup.opponent, probability

    ##
    ## learn_result
    ##
    def learn_result(self, winnerId:int, matchup:SumoMatchup, \
                     basho:SumoTournament, division:SumoDivision, \
                     day:int, DEBUG=False):
        if len(self._comphistory) != len(self._comparison):
            if DEBUG:
                sys.stdout.write(f'Resetting comparison history to have {len(self._comparison)} elements')
            # inditialize the _comphistory list
            self._comphistory = []
            for c in self._comparison:
                h = \
                    {'correct_predictions': 0.0, \
                     'wrong_predictions': 0.0, \
                     'sum_weight_correct': 0.0, \
                     'ravg_weight_correct': 0.0, \
                     'sum_weight_wrong': 0.0, \
                     'ravg_weight_wrong': 0.0}
                self._comphistory.append(h)
        #
        # Run through each comparison - do the prediction, then compare
        # against the actual winner and gather some stats.
        #
        for (c,h) in zip(self._comparison, self._comphistory):
            # divide by weight because calling the predictor automatically
            # multiplies by the arbitrary weight. That weight is exactly
            # what we are trying to influence / determine, so we need
            # to factor it out to investigate the efficacy of the comparison
            # itself.
            probability, _w = c(matchup, basho, division, day, DEBUG)
            if _w == 0.0:
                probability = 0.0
            else:
                probability = probability / _w

            # TODO: full stats on predictions
            if probability == 0.0:
                # predictor has no opinion here - skip to next one
                continue
            elif (probability > 0.0 and (matchup.rikishi.id() == winnerId)) or \
                 (probability < 0.0 and (matchup.opponent.id() == winnerId)):
                # successful prediction!
                h['correct_predictions'] += 1.0
                h['sum_weight_correct'] += abs(probability)
                if h['correct_predictions'] == 1.0:
                    h['ravg_weight_correct'] = abs(probability)
                else:
                    h['ravg_weight_correct'] = (h['ravg_weight_correct'] + \
                                                abs(probability)) / 2.0
            else:
                # unsuccessful prediction
                h['wrong_predictions'] += 1.0
                h['sum_weight_wrong'] += abs(probability)
                if h['wrong_predictions'] == 1.0:
                    h['ravg_weight_wrong'] = abs(probability)
                else:
                    h['ravg_weight_wrong'] = (h['ravg_weight_wrong'] + \
                                              abs(probability)) / 2.0
        return

    def get_comp_history(self):
        if len(self._comphistory) != len(self._comparison):
            return None
        out = {}
        for (c,h) in zip(self._comparison, self._comphistory):
            outstats = {}
            total = h['correct_predictions'] + h['wrong_predictions']

            correct = h['correct_predictions'] / total
            weight_correct = h['sum_weight_correct'] / h['correct_predictions']
            ravg_weight_correct = h['ravg_weight_correct']

            wrong= h['wrong_predictions'] / total
            weight_wrong = h['sum_weight_wrong'] / h['wrong_predictions']
            ravg_weight_wrong = h['ravg_weight_wrong']

            outstats = {'total':total, \
                        'correct':correct, 'wrong':wrong, \
                        'avg_weight_correct':weight_correct, \
                        'ravg_weight_correct':ravg_weight_correct, \
                        'weight_wrong':weight_wrong, \
                        'ravg_weight_wrong':ravg_weight_wrong}
            out[c.name()] = outstats
        return out

