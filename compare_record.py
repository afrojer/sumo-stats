#!/usr/bin/env python3
#
# compare_physical.py
#
# Define physical trait comparators
#
# Each class should have a compare() function that takes a single SumoMatchup parameter.
# This function should return:
#     [-1, 0) to favor "opponent"
#     (0, 1] to favor "rikishi"
#     0 to pass through with no opinion
#

import os
import sys
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)

from sumostats.sumodata import *
from sumostats.sumocalc import *

class CompareRank(SumoBoutCompare):
    def compare(self, matchup, basho, day):
        rRank = matchup.rikishi.rank(basho.id())
        rVal = RikishiRank.RankValue(rRank)
        oRank = matchup.opponent.rank(basho.id())
        oVal = RikishiRank.RankValue(oRank)

        # lower rank values are better rikishi
        _valDiff = -(float(rVal) - float(oVal))

        # rank values are in ~100 value ranges
        # the highest division has a spread from 519 - 101
        # assign a percentage based on a 300 point span
        # clamp values above or below
        _pct = _valDiff / 300.0
        return min(max(-1.0, _pct), 1.0)

class CompareBashoRecord(SumoBoutCompare):
    """
    Compare rikishi based on their current record in the basho.
    """
    def compare(self, matchup, basho, day):
        _rikishiRecord, r_div = basho.get_rikishi_record(matchup.rikishi.id())
        _opponentRecord, o_div = basho.get_rikishi_record(matchup.opponent.id())
        if not _rikishiRecord or not _opponentRecord:
            # don't compare if one or more of them doesn't have a record
            return 0.0
        rRecord = _rikishiRecord.get_record_on_day(day)
        oRecord = _opponentRecord.get_record_on_day(day)

        #
        # take the difference of win percentages: this will result
        # in a direct [-1, 1] range where 1.0 says the rikishi has won every
        # day so far and the opponent has lost every day, and -1.0 says the
        # opponent has won every day and the rikishi has lost every day
        #
        _winDiff = (float(rRecord.wins) / float(day)) - (float(oRecord.wins) / float(day))

        _boost = 0.0
        # boost if rikishi is on the edge of kachi-koshi or make-koshi
        # (they should fight harder)
        if rRecord.wins == 7 or rRecord.losses == 7:
            _boost += 0.1
        if oRecord.wins == 7 or oRecord.losses == 7:
            _boost -= 0.1

        # TODO: look at "hot streak" in current basho?

        _winDiff * (1.0 + _boost)
        return max(min(-1.0, _winDiff), 1.0)

class CompareHeadToHead(SumoBoutCompare):
    """
    Compare rikishi based on their head-to-head record
    """
    def compare(self, matchup, basho, day):
        # matchup.first_meeting
        # matchup.last_meeting

        _winPct = float(matchup.wins(no_fusensho=True)) / float(matchup.total_matches())

        # stretch the win percentage across a [-1, 1] range
        return ((2.0 * _winPct) - 1.0)

class CompareOverallRecord(SumoBoutCompare):
    """
    Compare rikishi based on their overall win/loss records
    """
    def compare(self, matchup, basho, day):
        # TODO: we should probably pre-calculate this...
        _wins = 0
        _total = 0
        for match in matchup.rikishi.each_match(self._data):
            if match.winnerId == matchup.rikishi.id():
                _wins += 1
            _total += 1

        if _total == 0:
            return 0.0

        _rWinPct = float(_wins) / float(_total)

        _wins = 0
        _total = 0
        for match in matchup.opponent.each_match(self._data):
            if match.winnerId == matchup.rikishi.id():
                _wins += 1
            _total += 1
        _oWinPct = float(_wins) / float(_total)

        return _rWinPct - _oWinPct

