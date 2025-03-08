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
    def compare(self, matchup, basho, division, day):
        rRank = matchup.rikishi.rank(basho.id_str())
        rVal = RikishiRank.RankValue(rRank)
        oRank = matchup.opponent.rank(basho.id_str())
        oVal = RikishiRank.RankValue(oRank)

        # lower rank values are better rikishi
        _valDiff = -(float(rVal) - float(oVal))

        # rank values are in ~100 value ranges
        # the highest division has a spread from 519 - 101
        # assign a percentage based on a 300 point span
        # clamp values above or below
        _pct = _valDiff / 300.0
        _pct = min(max(-1.0, _pct), 1.0)
        self.debug('RikishiRank:@rrank, OpponentRank:@orank, Diff:@diff, PCT:@pct', \
                   rrank=rRank, orank=oRank, diff=_valDiff, pct=_pct)
        return _pct

class CompareBashoRecord(SumoBoutCompare):
    """
    Compare rikishi based on their current record in the basho.
    """
    def compare(self, matchup, basho, division, day):
        _rikishiRecord, r_div = basho.get_rikishi_record(matchup.rikishi.id())
        _opponentRecord, o_div = basho.get_rikishi_record(matchup.opponent.id())
        if not _rikishiRecord or not _opponentRecord:
            # don't compare if one or more of them doesn't have a record
            self.debug('No records to compare')
            return 0.0
        rRecord = _rikishiRecord.get_record_on_day(day)
        oRecord = _opponentRecord.get_record_on_day(day)
        if not rRecord or not oRecord:
            self.debug('No records on day {day} to compare')
            return 0.0

        #
        # take the difference of win percentages: this will result
        # in a direct [-1, 1] range where 1.0 says the rikishi has won every
        # day so far and the opponent has lost every day, and -1.0 says the
        # opponent has won every day and the rikishi has lost every day
        #
        _winDiff = (float(rRecord.wins) / float(day)) - (float(oRecord.wins) / float(day))
        self.debug('RikishiWins:@rwins, OppWins:@owins, Diff:@diff', \
                   rwins=rRecord.wins, owins=oRecord.wins, diff=_winDiff)

        _boost = 0.0
        # boost if rikishi is on the edge of kachi-koshi or make-koshi
        # (they should fight harder)
        if rRecord.wins == 7 or rRecord.losses == 7:
            _boost += 0.2
            self.debug('Rikishi win/loss boost! (boost=@boost)', boost=_boost)
        if oRecord.wins == 7 or oRecord.losses == 7:
            _boost -= 0.2
            self.debug('Opponent win/loss boost! (boost=@boost)', boost=_boost)

        # Look at the rikishi to see if he's on a win-streak
        _rstreak = 0
        for _, br in _rikishiRecord.each_match(until=day):
            if br.result == SumoResult.WIN:
                _rstreak += 1
            else:
                _rstreak = 0
        # add a boost if the rikishi is on a streak
        # TODO: NOTE: this value is not very scientific... it's more of a guess
        _rboost = 0.5 * (float(_rstreak) / float(day))

        # Look at the opponent to see if he's on a win-streak
        _ostreak = 0
        for _, br in _opponentRecord.each_match(until=day):
            if br.result == SumoResult.WIN:
                _ostreak += 1
            else:
                _ostreak = 0
        # add a boost if the opponent is on a streak
        # TODO: NOTE: this value is not very scientific... it's more of a guess
        _oboost = 0.5 * (float(_ostreak) / float(day))

        _boost = _boost + _rboost - _oboost
        _pct = min(max(-1.0, _winDiff + _boost), 1.0)

        self.debug('RikishiBoost:@rboost (streak=@rstreak), OppBoost:@oboost (streak:@ostreak) PCT:@pct', \
                   rboost=_rboost, rstreak=_rstreak, oboost=_oboost, ostreak=_ostreak, \
                   pct=_pct)
        return _pct

class CompareHeadToHeadFull(SumoBoutCompare):
    """
    Compare rikishi based on their entire head-to-head record
    """
    def compare(self, matchup, basho, division, day):
        # TODO: use matchup.first_meeting?
        # TODO: use matchup.last_meeting?

        _rWins = matchup.wins(no_fusensho=True, beforeBasho=basho.date())
        _total = matchup.total_matches(no_fusen=True, beforeBasho=basho.date())

        if _total == 0:
            self.debug('No non-fusen head-to-head matches fought')
            return 0.0

        _winPct = float(_rWins) / float(_total)

        # stretch the win percentage across a [-1, 1] range
        _pct = ((2.0 * _winPct) - 1.0)

        self.debug('WinPct:@wpct [@rWins/@total], PCT:@pct', \
                   wpct=_winPct, rWins=_rWins, total=_total, pct=_pct)
        return _pct

class CompareHeadToHeadCurrentDivision(SumoBoutCompare):
    """
    Compare rikishi based on their head-to-head record in the current division
    """
    def compare(self, matchup, basho, division, day):

        # if matchup.rikishi and matchup.opponent are in different divisions
        # then we need to pick one. Let's 
        _rWins = matchup.wins(no_fusensho=True, beforeBasho=basho.date(), in_division=division)
        _total = matchup.total_matches(no_fusen=True, beforeBasho=basho.date(), in_division=division)

        if _total == 0:
            self.debug('No non-fusen head-to-head matches in {division} fought')
            return 0.0

        _winPct = float(_rWins) / float(_total)

        # stretch the win percentage across a [-1, 1] range
        _pct = ((2.0 * _winPct) - 1.0)

        self.debug('In:@div, WinPct:@wpct [@rWins/@total], PCT:@pct', \
                   div=division, wpct=_winPct, rWins=_rWins, total=_total, pct=_pct)
        return _pct

class CompareOverallRecord(SumoBoutCompare):
    """
    Compare rikishi based on their overall win/loss records
    """
    def compare(self, matchup, basho, division, day):
        # TODO: we should probably pre-calculate this...
        _wins = 0
        _total = 0
        for match in matchup.rikishi.each_match(self._data):
            if match.winnerId == matchup.rikishi.id():
                _wins += 1
            _total += 1

        if _total == 0:
            self.debug('Rikishi has no match data')
            return 0.0

        _rWinPct = float(_wins) / float(_total)

        _wins = 0
        _total = 0
        for match in matchup.opponent.each_match(self._data):
            if match.winnerId == matchup.opponent.id():
                _wins += 1
            _total += 1

        if _total == 0:
            self.debug('Opponent has no match data')
            return 0.0

        _oWinPct = float(_wins) / float(_total)

        _pct = _rWinPct - _oWinPct

        self.debug('RikishiWinPct:@rpct, OppWinPct:@opct, PCT:@pct', \
                   rpct=_rWinPct, opct=_oWinPct, pct=_pct)

        return _pct

