#!/usr/bin/env python3

from .sumodata import *

import json
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
    def __init__(self, data:SumoData, weight:float = 1.0, \
                 correct_confidence:float = 0.0, \
                 wrong_confidence:float = 0.0, \
                 weight_by_day:dict = {}, weight_by_month:dict = {}):
        self._data = data
        self._weight = weight
        self._correct_confidence = correct_confidence
        self._wrong_confidence = wrong_confidence
        self._DEBUG = False
        self._by_day = {}
        for k,v in weight_by_day.items():
            # make sure our keys are integer days,
            # and the value is a list >= 2 elements
            if isinstance(v, list) and len(v) > 1:
                self._by_day[int(k)] = v
        self._by_month = {}
        for k,v in weight_by_month.items():
            # make sure our keys are integer months,
            # and the value is a list >= 2 elements
            if isinstance(v, list) and len(v) > 1:
                self._by_month[int(k)] = v
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

    def correct_confidence(self) -> float:
        return self._correct_confidence

    def wrong_confidence(self) -> float:
        return self._wrong_confidence

    def weight_by_day(self, day) -> float:
        if day in self._by_day:
            return self._by_day[day][0]
        return 0.0

    def correct_confidence_by_day(self, day) -> float:
        if day in self._by_day:
            return self._by_day[day][1]
        return 0.0

    def wrong_confidence_by_day(self, day) -> float:
        if day in self._by_day and len(self._by_day[day]) > 2:
            return self._by_day[day][2]
        return 0.0

    def weight_by_month(self, month) -> float:
        if month in self._by_month:
            return self._by_month[month][0]
        return 0.0

    def correct_confidence_by_month(self, month) -> float:
        if day in self._by_month:
            return self._by_month[month][1]
        return 0.0

    def wrong_confidence_by_month(self, month) -> float:
        if day in self._by_month and len(self._by_month[month]) > 2:
            return self._by_month[month][2]
        return 0.0
    #def threshold_by_month(self, month) -> float:
    #    if month in self._by_month:
    #        return self._by_month[month][1]
    #    return 0.0

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

        ## TODO: use _pct thresholds based on average weight (confidence) when correct...
        ##       e.g. maybe use a day weight when the confidence is higher than the overall?

        _cc = self.correct_confidence()
        _wc = self.wrong_confidence()

        dayweight = self.weight_by_day(day)
        if dayweight > 0.0:
            self.debug('ByDay[@day]=@wday (weight=@weight):  @pct', day=day, wday=dayweight, weight=_w, pct=_pct )
            _w = dayweight
            _cc = self.correct_confidence_by_day(day)
            _wc = self.wrong_confidence_by_day(day)

        if _cc > _wc:
            _diff = _cc - _wc
            if abs(_pct) > _wc:
                #_w *= 1.0 + _diff
                #_w *= 2.0*random.random() - 1.0
                _w *= 1.0 + (abs(_pct) - _wc)
                #self.debug('WONKYCONFIDENCE: pct=@pct new_weight:@wgt (old_weight:@owgt) (diff=@diff)', pct=_pct, wgt=_w, owgt=self._weight, diff=_diff)

        result = result * _w

        self._DEBUG = False
        return result, _w


##
## PredictionHistory
##
class PredictionHistory:
    """
    PredictionHistory

    This class is used when analyzing the accuracy of comparisons and
    predictions use the learn_result() function of the SumoBoutPredictor
    """
    def __init__(self):
        self.total_predictions = 0.0

        self.correct_predictions = 0.0
        self.sum_weight_correct = 0.0
        self.ravg_weight_correct = 0.0

        self.wrong_predictions = 0.0
        self.sum_weight_wrong = 0.0
        self.ravg_weight_wrong = 0.0

        self.by_day:dict[int, PredictionHistory] = {}
        self.by_month:dict[int, PredictionHistory] = {}

    def __str__(self):
        s = '{ '
        s += f'Correct[{int(self.correct_predictions)}/{int(self.total_predictions)}={self.pct_correct():.2%}, ' + \
             f'avgW={self.weight_correct_average():.3}, ravgW={self.weight_correct_running_average():.3}], '
        s += f'Wrong[{int(self.wrong_predictions)}/{int(self.total_predictions)}={self.pct_wrong():.2%}, ' + \
             f'avgW={self.weight_wrong_average():.3}, ravgW={self.weight_wrong_running_average():.3}]'
        nl = False
        for day, h in self.by_day.items():
            s += f'\n\t  Day {day}:{str(h)}'
            nl = True
        for month, h in self.by_month.items():
            s += f'\n\t  Month {month}:{str(h)}'
            nl = True
        if nl:
            s+= '\n\t'
        s += ' }'
        return s

    #
    # TODO: full stats on predictions (mean, median, etc)
    #

    def add_correct(self, weight:float, basho:SumoTournament = None, day:int = -1) -> None:
        self.total_predictions += 1.0
        self.correct_predictions += 1.0
        self.sum_weight_correct += abs(weight)
        if self.correct_predictions == 1.0:
            self.ravg_weight_correct = abs(weight)
        else:
            self.ravg_weight_correct = (self.ravg_weight_correct + abs(weight)) / 2.0

        # keep per-day history
        if day >= 1:
            if not day in self.by_day:
                self.by_day[day] = PredictionHistory()
            self.by_day[day].add_correct(weight)

        # keep per-month history as well
        if basho:
            month = basho.date().month
            if not month in self.by_month:
                self.by_month[month] = PredictionHistory()
            self.by_month[month].add_correct(weight)

    def add_wrong(self, weight:float, basho:SumoTournament = None, day:int = -1) -> None:
        self.total_predictions += 1.0
        self.wrong_predictions += 1.0
        self.sum_weight_wrong += abs(weight)
        if self.wrong_predictions == 1.0:
            self.ravg_weight_wrong = abs(weight)
        else:
            self.ravg_weight_wrong = (self.ravg_weight_wrong + abs(weight)) / 2.0

        # keep per-day history
        if day >= 1:
            if not day in self.by_day:
                self.by_day[day] = PredictionHistory()
            self.by_day[day].add_wrong(weight)

        # keep per-month history as well
        if basho:
            month = basho.date().month
            if not month in self.by_month:
                self.by_month[month] = PredictionHistory()
            self.by_month[month].add_wrong(weight)

    def total(self) -> float:
        return self.total_predictions

    def distance_from_p50(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return self.pct_correct() - 0.50

    def pct_correct(self) -> float:
        if self.total_predictions == 0.0:
            return 0.0
        return self.correct_predictions / self.total_predictions

    def weight_correct_average(self) -> float:
        if self.total_predictions == 0.0:
            return 0.0
        if self.correct_predictions == 0.0:
            return 0.0
        return self.sum_weight_correct / self.correct_predictions

    def weight_correct_running_average(self) -> float:
        return self.ravg_weight_correct

    def pct_wrong(self) -> float:
        if self.total_predictions == 0.0:
            return 0.0
        return self.wrong_predictions / self.total_predictions

    def weight_wrong_average(self) -> float:
        if self.total_predictions == 0.0:
            return 0.0
        if self.wrong_predictions == 0.0:
            return 0.0
        return self.sum_weight_wrong / self.wrong_predictions

    def weight_wrong_running_average(self) -> float:
        return self.ravg_weight_wrong

    def each_day(self):
        for day, h in self.by_day.items():
            yield day, h

    def each_month(self):
        for month, h in self.by_month.items():
            yield month, h

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
        self._comphistory: list[PredictionHistory] = []

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
                h = PredictionHistory()
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

            if probability == 0.0:
                # predictor has no opinion here - skip to next one
                continue
            elif (probability > 0.0 and (matchup.rikishi.id() == winnerId)) or \
                 (probability < 0.0 and (matchup.opponent.id() == winnerId)):
                # successful prediction!
                h.add_correct(probability, basho, day)
            else:
                # unsuccessful prediction
                h.add_wrong(probability, basho, day)
        return

    def get_comp_history(self) -> dict[str, PredictionHistory]:
        if len(self._comphistory) != len(self._comparison):
            return None
        out = {}
        for (c,h) in zip(self._comparison, self._comphistory):
            out[c.name()] = h
        return out

    def construct_suggested_weights(self):
        # for each comparison, look at the total win percentage. If it's above
        # 50%, save the difference between that percentage and 50% and
        # accumulate the value as a total "confidence weight", then calculate
        # the weight each comparison has against the total "confidence weight".
        #
        # Do this for each day and bash month
        #
        weights = {}
        total_weight = 0.0
        total_weight_by_day = {}
        total_weight_by_month = {}
        for (c,h) in zip(self._comparison, self._comphistory):
            weights[c.name()] = { "weight": 0.0, "correct_confidence": 0.0, "wrong_confidence": 0.0, "by_day": {}, "by_month": {} }
            _dist = h.distance_from_p50()
            if _dist > 0.0:
                total_weight += _dist
                weights[c.name()]["weight"] = _dist
                weights[c.name()]["correct_confidence"] = h.weight_correct_average()
                weights[c.name()]["wrong_confidence"] = h.weight_wrong_average()

            # Look at each day
            for day, dayhist in h.each_day():
                _dist = dayhist.distance_from_p50()
                if _dist > 0.0:
                    if not day in total_weight_by_day:
                        total_weight_by_day[day] = _dist
                    else:
                        total_weight_by_day[day] += _dist
                    weights[c.name()]["by_day"][day] = [ _dist, dayhist.weight_correct_average(), dayhist.weight_wrong_average() ]

            # Look at each month
            for month, month_hist in h.each_month():
                _dist = month_hist.distance_from_p50()
                if _dist > 0.0:
                    if not month in total_weight_by_month:
                        total_weight_by_month[month] = _dist
                    else:
                        total_weight_by_month[month] += _dist
                    weights[c.name()]["by_month"][month] = [ _dist, month_hist.weight_correct_average(), month_hist.weight_wrong_average() ]

        # run through each one again to caclulate relative weights from the
        # total weight of >50% predictions
        for (c,h) in zip(self._comparison, self._comphistory):
            _w = weights[c.name()]["weight"]
            if _w > 0.0:
                weights[c.name()]["weight"] = 100.0 * (_w / total_weight)
            # now for each day
            for day, dayhist in h.each_day():
                if day in weights[c.name()]["by_day"]:
                    _w = weights[c.name()]["by_day"][day][0]
                    weights[c.name()]["by_day"][day][0] = 100.0 * (_w / total_weight_by_day[day])
            # now for each month
            for month, month_hist in h.each_month():
                if month in weights[c.name()]["by_month"]:
                    _w = weights[c.name()]["by_month"][month][0]
                    weights[c.name()]["by_month"][month][0] = 100.0 * (_w / total_weight_by_month[month])

        return weights

