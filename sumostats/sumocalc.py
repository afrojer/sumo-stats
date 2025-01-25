#!/usr/bin/env python3

from .sumodata import *

import random
from datetime import date
from dateutil.relativedelta import *
import sys

class SumoBoutCompare():
    """
    SumoBoutCompare

    Base class for generating a probability of the outcome of a bout. To create a comparator,
    derive a new class, and override the compare() method. In that method, you can use
    self._data as a SumoData object if you need additional context.

    """
    def __init__(self, data:SumoData, weight:float = 1.0):
        self._data = data
        self._weight = weight
        if not self._data:
            raise Exception('data cannot be empty/None')

    def compare(self, matchup:SumoMatchup, basho:SumoTournament, day:int):
        """
        Override this method

        Return:
          [-1, 0) to favor opponent
          (0, 1] to favor rikishi
          [0] to pass-through with no opinion about this matchup
        """
        pass

    def weight(self):
        return self._weight

    def __call__(self, matchup:SumoMatchup, basho:SumoTournament, day:int):
        return self.compare(matchup, basho, day) * self._weight


class SumoBoutPredictor():
    """
    BoutPredictor

    This class holds a list of comparisons, each of which generate a probability of bout
    outcome. The predict() function takes a SumoMatchup object and returns a predicted
    Rikishi winner along with a confidence (float).

    """
    def __init__(self, data:SumoData, comparison:list[SumoBoutCompare] = []):
        self._data = data
        self._comparison = comparison

    def add_comparison(self, compare:SumoBoutCompare):
        """
        Add a single bout comparison object to the predictor
        """
        self._comparison.append(compare)
        return

    def add_comparisons(self, compare:list[SumoBoutCompare]):
        """
        Add a list of bout comparison objects to the predictor
        """
        self._comparison.extend(compare)
        return

    def predict(self, matchup:SumoMatchup, basho:SumoTournament, day:int) -> {SumoWrestler, float}:
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
            # sys.stderr.write(f'No comparisons to make: randomly choosing\n')
            probability = 2.0*random.random() - 1.0
        else:
            weight = 0.0
            for c in self._comparison:
                probability += c(matchup, basho, day)
                weight += c.weight()
            probability = probability / weight

        if probability >= 0.0:
            # favor the Rikishi in an even match (exactly 0.0)
            return matchup.rikishi, probability
        else:
            return matchup.opponent, probability

