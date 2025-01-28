#!/usr/bin/env python3

from .sumoapi import *

from datetime import date
from dateutil.relativedelta import *
import pickle
import sys

class SumoWrestler():
    def __init__(self, r: Rikishi, s: RikishiStats):
        self.rikishi: Rikishi = r
        self.stats: RikishiStats = s

        # 'str' is the matchId: data can be found in the SumoData.matches
        self.all_matches: list[str] = []
        self.matches_by_opponent: dict[int, list[str]] = {}
        return

    def __str__(self):
        return f'{self.shikonaEn()}({self.rikishi.id})'

    def id(self) -> int:
        return self.rikishi.id

    def height(self) -> float:
        return self.rikishi.height

    def weight(self) -> float:
        return self.rikishi.weight

    def bmi(self) -> float:
        return self.rikishi.bmi

    def age(self, inBasho:date = None) -> float:
        return float(self.rikishi.age(inBasho))

    def shikonaEn(self, bashoDate:date = None):
        if not bashoDate:
            return self.rikishi.shikonaEn

        bashoShikona = self.rikishi.shikonaEn
        for shikona in sorted(self.rikishi.shikonaHistory, key=lambda s: s.bashoId):
            if shikona.bashoId < bashoDate:
                bashoShikona = shikona
        return bashoShikona

    def rank(self, bashoId = None):
        if not bashoId:
            return self.rikishi.currentRank

        _bashoDate = BashoDate(bashoId)
        bashoRank = self.rikishi.currentRank
        for rank in sorted(self.rikishi.rankHistory, key=lambda r: r.bashoId):
            if rank.bashoId < _bashoDate:
                bashoRank = rank.rank
        return bashoRank

    def rankValue(self, bashoId = None):
        if not bashoId:
            return self.rikishi.currentRankValue

        _bashoDate = BashoDate(bashoId)
        bashoRank = self.rikishi.currentRankValue
        for rank in sorted(self.rikishi.rankHistory, key=lambda r: r.bashoId):
            if rank.bashoId < _bashoDate:
                bashoRank = rank.rankValue
        return bashoRank

    def get_rank_history(self) -> list[RikishiRank]:
        return sorted(self.rikishi.rankHistory)

    def each_match(self, data):
        for mstr in self.all_matches:
            yield data.get_match(mstr)


class SumoMatchup():
    def __init__(self, data, rikishi:SumoWrestler, opponent:SumoWrestler):
        self.rikishi = rikishi
        self.opponent = opponent
        self.first_meeting = datetime.now().date()
        self.last_meeting = date(1,1,1)

        self._overall = RikishiMatchup()
        self._by_division: dict[SumoDivision, RikishiMatchup] = {}
        self._by_rank: dict[str, RikishiMatchup] = {}

        if not opponent.id() in self.rikishi.matches_by_opponent:
            return

        matchlist = self.rikishi.matches_by_opponent[opponent.id()]

        overall = self._overall

        # map each matchId string to a BashoMatch object and collect them into a list
        all_matches = list(map(lambda m: data.matches.get(m), matchlist))

        for m in all_matches:
            # keep track of first and last meeting dates (basho)
            if m.bashoId < self.first_meeting:
                self.first_meeting = m.bashoId
            if m.bashoId > self.last_meeting:
                self.last_meeting = m.bashoId

            if not m.division in self._by_division:
                self._by_division[m.division] = RikishiMatchup()
            division = self._by_division[m.division]

            rank = ''
            if m.eastId == rikishi.id():
                rank = m.eastRank
            else:
                rank = m.westRank
            if not rank in self._by_rank:
                self._by_rank[rank] = RikishiMatchup()
            byrank = self._by_rank[rank]

            matchuplist = [overall, division, byrank]
            for matchup in matchuplist:
                # match totals and list by division and rank (of Rikishi)
                matchup.total += 1
                matchup.matches.append(m)

            if m.winnerId == rikishi.id():
                for matchup in matchuplist:
                    matchup.rikishiWins += 1
                    if not m.kimarite in matchup.kimariteWins:
                        matchup.kimariteWins[m.kimarite] = 1
                    else:
                        matchup.kimariteWins[m.kimarite] += 1
            else:
                for matchup in matchuplist:
                    matchup.opponentWins+= 1
                    if not m.kimarite in matchup.kimariteLosses:
                        matchup.kimariteLosses[m.kimarite] = 1
                    else:
                        matchup.kimariteLosses[m.kimarite] += 1

    #
    # Get matchup (stats) objects
    # Iterate over matchup objects by divisions and ranks
    # 

    def matchup_overall(self) -> RikishiMatchup:
        return self._overall

    def matchup_by_division(self, division:SumoDivision) -> RikishiMatchup:
        if not division in self._by_division:
            return RikishiMatchup()
        return self._by_division[division]

    def each_division(self):
        for matchup in self._by_division.items():
            yield matchup[0], matchup[1]

    def matchup_by_rank(self, rank:str) -> RikishiMatchup:
        if not rank in self._by_rank:
            return RikishiMatchup()
        return self._by_rank[rank]

    def each_rank(self):
        for matchup in self._by_rank.items():
            yield matchup[0], matchup[1]

    def each_match(self, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        """
        Generator to iterate over each match the rikishi and opponent have fought.
        You can filter the matches to iterate over using the
        'beforeBasho', 'in_division', and 'at_rank' parameters
        """
        # Allow ranks to be passed as strings or ints
        rankVal = -1
        if at_rank and is_instance(at_rank, str):
            rankVal = RikishiRank.RankValue(at_rank)
        elif at_rank:
            rankVal = int(at_rank)

        # run through all matches, and filter/yield based on the input
        for match in sorted(self._overall.matches, key=lambda m: m.bashoId, reverse=True):
            # set this to false if a one of the inputs would 
            # filter out the current match
            should_yield = True

            if beforeBasho and match.bashoId >= beforeBasho:
                should_yield = False
            elif in_division and not match.division == in_division:
                should_yield = False
            elif rankVal > 0:
                if (match.eastId == self.rikishi.id()) and (rankVal != RikishiRank.RankValue(match.eastRank)):
                    should_yield = False
                if (match.westId == self.rikishi.id()) and (rankVal != RikishiRank.RankValue(match.westRank)):
                    should_yield = False
            if should_yield:
                yield match

    #
    # Get single values (with filters)
    #

    def total_matches(self, no_fusen=False, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        if not beforeBasho and not in_division and not at_rank:
            # this is the simple case where we can just grab a number
            if no_fusen and str(SumoResult.FUSEN) in self._overall.kimariteWins:
                return self._overall.total - self._overall.kimariteWins[str(SumoResult.FUSEN)]
            return self._overall.total

        # We have to do some filtering, so run through every match
        # fortunately, this generator does most of the filtering!
        _total = 0
        for match in self.each_match(beforeBasho=beforeBasho, in_division=in_division, at_rank=at_rank):
            if no_fusen and match.kimarite == str(SumoResult.FUSEN):
                pass
            else:
                _total += 1
        return _total

    def wins(self, no_fusensho=False, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        wins = self._overall.rikishiWins
        if no_fusensho:
            if str(SumoResult.FUSEN) in self._overall.kimariteWins:
                wins -= self._overall.kimariteWins[str(SumoResult.FUSEN)]
        # easy case: no filtering
        if not beforeBasho and not in_division and not at_rank:
            return wins

        # use the each_match generator to filter for us
        wins = 0
        for match in self.each_match(beforeBasho=beforeBasho, in_division=in_division, at_rank=at_rank):
            if match.winnerId == self.rikishi.id():
                if no_fusensho and match.kimarite == str(SumoResult.FUSEN):
                    pass
                else:
                    wins += 1
        return wins

    def fusensho(self, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        if not beforeBasho and not in_division and not at_rank:
            if str(SumoResult.FUSEN) in self._overall.kimariteWins:
                return self._overall.kimariteWins[str(SumoResult.FUSEN)]
            return 0
        else:
            fusen = 0
            for match in self.each_match(beforeBasho=beforeBasho, in_division=in_division, at_rank=at_rank):
                if match.kimarite == str(SumoResult.FUSEN) and match.winnerId == self.rikishi.id():
                    fusen += 1
            return fusen

    def losses(self, no_fusenpai=False, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        losses = self._overall.opponentWins
        if no_fusenpai:
            if str(SumoResult.FUSEN) in self._overall.kimariteLosses:
                losses -= self._overall.kimariteLosses[str(SumoResult.FUSEN)]
        # easy case: no filtering
        if not beforeBasho and not in_division and not at_rank:
            return losses

        # use the each_match generator to filter for us
        losses = 0
        for match in self.each_match(beforeBasho=beforeBasho, in_division=in_division, at_rank=at_rank):
            if not (match.winnerId == self.rikishi.id()):
                if no_fusenpai and match.kimarite == str(SumoResult.FUSEN):
                    pass
                else:
                    losses += 1
        return losses

    def fusenpai(self, beforeBasho:date = None, in_division:SumoDivision = None, at_rank = None):
        if not beforeBasho and not in_division and not at_rank:
            if str(SumoResult.FUSEN) in self._overall.kimariteLosses:
                return self._overall.kimariteLosses[str(SumoResult.FUSEN)]
            return 0
        else:
            fusen = 0
            for match in self.each_match(beforeBasho=beforeBasho, in_division=in_division, at_rank=at_rank):
                if match.kimarite == str(SumoResult.FUSEN) and not (match.winnerId == self.rikishi.id()):
                    fusen += 1
            return fusen

class SumoRecord():
    def __init__(self, wins = 0, losses = 0, absences = 0):
        self.wins = wins
        self.losses = losses
        self.absences = absences

class SumoBanzukeRikishi():
    def __init__(self, record:BanzukeRikishi):
        self.record_on_day: dict[int, SumoRecord] = {}
        self.result_on_day: dict[int, SumoResult] = {}
        self.opponent_on_day: dict[int, int] = {}

        # TODO: de-dup the BashoTorikumi for lower memory usage when un-pickling?
        self.match_on_day: dict[int, BashoMatch] = {}

        self.rikishiId = record.rikishiId
        self.rank = record.rank
        self.rankValue = record.rankValue
        self.side = record.side
        self.wins = record.wins
        self.losses = record.losses
        self.absences = record.absences
        # these are not guaranteed to be unordered, so unfortunately we can't infer any by-day stats
        self.match_record:list[BanzukeMatchRecord] = record.record
        # we will order them as individual matches are set
        self.match_record_by_day:dict[int, BanzukeMatchRecord] = {}
        return

    def get_record_on_day(self, day:int) -> SumoRecord:
        if day in self.record_on_day:
            return self.record_on_day[day]
        return None

    def get_result_on_day(self, day:int) -> SumoResult:
        if not day in self.result_on_day:
            return SumoResult.UNKNOWN
        return self.result_on_day[day]

    def add_match(self, match:BashoMatch):
        day = match.day
        self.match_on_day[day] = match

        opponent = match.eastId
        if self.rikishiId == match.eastId:
            opponent = match.westId
        self.opponent_on_day[day] = opponent

        # Find the BanzukeMatchRecord for this day (based on opponent)
        # this isn't perfect, but iterating through the list from start
        # to finish should get us close enough b/c facing the same rikishi
        # more than once in a tournament should be rare
        for r in self.match_record:
            if r.opponentID == opponent:
                self.match_record_by_day[day] = r
                break

        _result = SumoResult.UNKNOWN
        _wins = 0
        _losses = 0
        _absences = 0
        # Run through each day and re-calculate the record on that day
        for d in range(1, len(self.match_record) + 1):
            if d in self.match_on_day:
                # found a record on this day
                if self.match_on_day[d].winnerId == self.rikishiId:
                    # we won!
                    _wins += 1
                    _result = SumoResult.WIN
                    if self.match_on_day[d].kimarite == str(SumoResult.FUSEN):
                        _result = SumoResult.FUSENSHO
                else:
                    # we didn't win: check if the loss was "fusen" to
                    # accurately count absences vs. losses
                    if self.match_on_day[d].kimarite == str(SumoResult.FUSEN):
                        _absences += 1
                        _result = SumoResult.FUSENPAI
                    else:
                        _losses += 1
                        _result = SumoResult.LOSS
            else:
                # no record on this day yet? Count it as an absence
                _absences += 1
                _result = SumoResult.ABSENT
            self.record_on_day[d] = SumoRecord(_wins, _losses, _absences)
            self.result_on_day[d] = _result
        return

    def each_match(self, until:int = 0):
        for day in range(1, len(self.match_record) + 1):
            if until > 0 and day > until:
                return
            if not day in self.match_record_by_day:
                # yield an empty record if we don't know about this day (yet)
                yield day, BanzukeMatchRecord()
            else:
                yield day, self.match_record_by_day[day]
        return

class SumoBanzuke():
    def __init__(self, b:Banzuke):
        self.bashoId = b.bashoId
        self.division = b.division
        self.rikishi: dict[int, SumoBanzukeRikishi] = {}

        # re-index the Banzuki records into something more easily queried
        if b.east:
            for r in b.east:
                self.rikishi[r.rikishiId] = SumoBanzukeRikishi(r)
        if b.west:
            for r in b.west:
                self.rikishi[r.rikishiId] = SumoBanzukeRikishi(r)
        return

    def get_record(self, rID) -> SumoBanzukeRikishi:
        if not rID in self.rikishi:
            return None
        return self.rikishi[rID]

    def get_record_on_day(self, rID, day) -> SumoRecord:
        if not rID in self.rikishi:
            return None
        return self.rikishi[rID].get_record_on_day(day)

    def add_torikumi(self, day:int, torikumi:list[BashoMatch]):
        for match in torikumi:
            rId = match.eastId
            if rId in self.rikishi:
                self.rikishi[rId].add_match(match)
            rId = match.westId
            if rId in self.rikishi:
                self.rikishi[rId].add_match(match)
        return

class SumoTournament():
    def __init__(self, b:Basho):
        self.basho: Basho = b
        self.rikishi: list[int] = []
        self.banzuke: dict[SumoDivision, SumoBanzuke] = {}

        # TODO: de-dup the BashoTorikumi for lower memory usage when un-pickling?

        # The Torikumi is the list of matches (and results)
        self.torikumi_by_division: dict[SumoDivision, dict[int, list[BashoMatch]]] = {}
        self.torikumi_by_day: dict[int, dict[SumoDivision, list[BashoMatch]]] = {}
        return

    def id_str(self):
        return self.basho.id_str()

    def date(self):
        return BashoDate(self.basho.id_str())

    def num_days(self):
        return len(self.torikumi_by_day.keys())

    def get_banzuke(self, division: SumoDivision) -> SumoBanzuke:
        if not division in self.banzuke:
            return None
        return self.banzuke[division]

    def get_bouts_by_day_in_division(self, division) -> dict[int, list[BashoMatch]]:
        if division not in self.torikumi_by_division:
            return None
        return self.torikumi_by_division[division]

    def get_bouts_by_division_on_day(self, day) -> dict[SumoDivision, list[BashoMatch]]:
        if not day in self.torikumi_by_day:
            return None
        return self.torikumi_by_day[day]

    def get_bouts_in_division_on_day(self, division, day) -> list[BashoMatch]:
        if not day in self.torikumi_by_day:
            return None
        if division not in self.torikumi_by_division:
            return None
        return self.torikumi_by_day[day][division]

    def get_upcoming_bouts(self, division) -> {int, list[BashoMatch]}:
        bouts = self.get_bouts_by_day_in_division(division)
        if not bouts:
            return 0, []
        for day in sorted(bouts.keys()):
            matchlist = bouts[day]
            print(f'Day {day} bouts:{len(matchlist)}')
            if len(matchlist) > 0 and matchlist[0].upcoming():
                return day, matchlist
        return 0, []

    def get_rikishi_record(self, rikishiId: int) -> {SumoBanzukeRikishi, SumoDivision}:
        """
        Retrieve the record for a wrestler in this tournament
        return SumoBanzukiRikishi, SumoDivision
        """
        if not rikishiId in self.rikishi:
            return None, None

        # the rikishi fought in this tournament - look through the banzuke to
        # find their record
        for div in (SumoDivision):
            d = SumoDivision(div.value)
            if d in self.banzuke:
                r = self.banzuke[d].get_record(rikishiId)
                if r:
                    return r, div.value

        # sys.stderr.write(f'LookupError: did not find rikishiId:{rikishiId} in any division in {self.id_str()} (but they competed?)\n')
        return None, None

class SumoData:
    """ Build a database of sumo wrestlers and match data """

    def __init__(self):
        self.api = SumoAPI()
        self.rikishi: dict[int, SumoWrestler] = {}
        self.basho: dict[date, SumoTournament] = {}
        self.matches: dict[str, BashoMatch] = {}
        return

    """
    Public Methods

    """
    def print_table_stats(self):
        print(f'SumoData[rikishi={len(self.rikishi.values())}, basho={len(self.basho.values())}, matches={len(self.matches.values())}]')
        return

    def get_basho(self, bashoStr, division=SumoDivision.UNKNOWN, fetch=False) -> SumoTournament:
        d = BashoDate(bashoStr)
        if fetch:
            self.update_basho(d, division=division)
        if not d in self.basho:
            return None
        return self.basho[d]

    def get_match(self, matchStr) -> BashoMatch:
        if not matchStr in self.matches:
            return None
        return self.matches[matchStr]

    def get_rikishi(self, rikishiId) -> SumoWrestler:
        if not rikishiId in self.rikishi:
            return None
        return self.rikishi[rikishiId]

    def find_rikishi(self, shikonaEn):
        for r in self.rikishi:
            if self.rikishi[r].shikonaEn() == shikonaEn:
                return self.rikishi[r]
        # Try a fuzzy match and return the first thing we find
        for r in self.rikishi:
            if shikonaEn in self.rikishi[r].shikonaEn():
                return self.rikishi[r]
        return None

    def get_matchup(self, rikishi:int, opponent:int):
        """
        Create a SumoMatchup object for all bouts between the specified rikishi and opponent
        """
        if not rikishi in self.rikishi:
            sys.stderr.write(f'Unknown rikishiId:{rikishi}\n')
            return None
        if not opponent in self.rikishi:
            sys.stderr.write(f'Unknown opponentId:{opponent}\n')
            return None

        return SumoMatchup(self, self.rikishi[rikishi], self.rikishi[opponent])

    def get_rikishi_basho_record(self, rikishiId, bashoStr) -> {list[SumoBanzukeRikishi], SumoDivision}:
        """
        Get the record of a rikishi in a specific basho.
        Returns a pair: list[SumoBanzukeRikishi], SumoDivision
        """
        if not rikishiId in self.rikishi:
            return [], SumoDivision.Unknown

        bashoDate = BashoDate(bashoStr)
        if not bashoDate in self.basho:
            return [], SumoDivision.Unknown

        return self.basho[bashoDate].get_rikishi_record(rikishiId)

    def get_rikishi_basho_record_by_day(self, rikishiId, bashoStr, day):
        return

    def load_data(path):
        """ Load a SumoData from a file """
        f = open(path, 'rb')
        try:
            table = pickle.load(f)
        except:
            table = None
        f.close()
        if not isinstance(table, SumoData):
            raise Exception(f'Invalid saved table file at {path}: not a SumoData')
        return table

    def save_data(self, path):
        """ Save SumoData instance to a file """
        f = open(path, 'wb')
        pickle.dump(self, f)
        f.close()
        return

    def update_basho(self, bashoDate: date, division: SumoDivision = SumoDivision.UNKNOWN):
        """
        Update information in the table with date pulled fresh from the API data source.
        This is most useful for in-progress tournaments.
        """
        basho = self.api.basho(BashoIdStr(bashoDate))
        if not basho or not basho.isValid():
            sys.stderr.write(f'Could not query basho:{bashoDate}\n')
            return
        self._add_basho(basho, division, forceUpdate=True)
        return

    def add_basho_by_date_range(self, startDate: date, endDate: date, division: SumoDivision = SumoDivision.UNKNOWN):
        # sanity check the dates
        if endDate < startDate:
            raise Exception('endDate:{endDate} must be later than startDate:{startDate}')

        # Find the closest date which successfully returns a basho
        bashoDate = startDate.replace(day=1)
        basho = None
        while True:
            basho = self.api.basho(BashoIdStr(bashoDate))
            if (basho and basho.isValid()) or bashoDate > endDate:
                break
            bashoDate = bashoDate + relativedelta(months=1)

        if bashoDate > endDate:
            sys.stderr.write(f'Could not find a basho between {startDate} and {endDate}\n')
            return

        # Iterate through the specified dates finding all Basho (in the division)
        #
        # First add the valid basho, then look for the next one, but don't add
        # it until we've checked that the bashoDate is within the specified
        # time period (in the next loop iteration)
        while bashoDate < endDate:
            if basho and basho.isValid():
                self._add_basho(basho, division)
            # tournaments are held every 2 months, but let's increment by one
            # month just in case things got offset
            bashoDate = bashoDate + relativedelta(months=1)
            basho = self.api.basho(BashoIdStr(bashoDate))
        return

    """
    Iteration Methods

    """
    def total_rikishi(self):
        return len(self.rikishi)

    def each_rikishi(self):
        for rikishi in self.rikishi.items():
            yield rikishi[1]

    def total_basho(self):
        return len(self.basho)

    def each_basho(self):
        for basho in self.basho.items():
            yield basho[1]

    """
    Private Methods

    """

    def _add_basho(self, b: Basho, division: SumoDivision, forceUpdate = False):
        if not b or not b.isValid():
            return

        tournament = None
        if b.bashoDate in self.basho:
            # Assume we already know about this one
            if not forceUpdate:
                sys.stderr.write(f'Skipping tournament: {b.id_str()} (already in table)\n')
                return
            sys.stderr.write(f'Updating tournament: {b.id_str()} (from API source)\n')
            tournament = self.basho[b.bashoDate]
            tournament.basho = b
        else:
            sys.stdout.write(f'Add New SumoTournament: {b.id_str()}\n')
            # Add this basho to our table as a set of Tournament objects
            tournament = SumoTournament(b)

        # retrieve the set of banzuke for this basho
        if division == SumoDivision.UNKNOWN:
            for div in (SumoDivision):
                if div != SumoDivision.UNKNOWN:
                    self._add_banzuke(tournament, div.value, forceUpdate)
        else:
            self._add_banzuke(tournament, division, forceUpdate)

        # add the tournament to our table
        self.basho[b.bashoDate] = tournament
        return

    def _add_banzuke(self, tournament: SumoTournament, division: SumoDivision, forceUpdate = False):
        sys.stdout.write(f'Query Banzuke for {division} (in {tournament.id_str()})\n')
        # Use the API to grab banzuke info
        banzuke = self.api.basho_banzuke(tournament.id_str(), division)
        if not banzuke:
            sys.stderr.write(f'    ERROR: No {division} banzuke found for basho:{tournament.id_str()}')
            return

        # Updates will just replace the banzuke
        tournament.banzuke[division] = SumoBanzuke(banzuke)

        max_bouts = 0

        # iterate over banzuke Rikishi
        if banzuke.east:
            for rikishi in banzuke.east:
                self._add_rikishi_banzuke_record(rikishi, tournament, forceUpdate)
                if max_bouts < len(rikishi.record):
                    max_bouts = len(rikishi.record)
                #bouts = rikishi.wins + rikishi.losses + rikishi.absences
                #if bouts > max_bouts:
                #    max_bouts = bouts
        else:
            sys.stderr.write(f'No east side in banzuke:{banzuke}\n')

        if banzuke.west:
            for rikishi in banzuke.west:
                self._add_rikishi_banzuke_record(rikishi, tournament, forceUpdate)
                if max_bouts < len(rikishi.record):
                    max_bouts = len(rikishi.record)
                #bouts = rikishi.wins + rikishi.losses + rikishi.absences
                #if bouts > max_bouts:
                #    max_bouts = bouts
        else:
            sys.stderr.write(f'No west side in banzuke:{banzuke}\n')

        # For each day of the tournament, add the torikumi
        for day in range(1, max_bouts+1):
            self._add_torikumi(tournament, division, day)

        return

    def _add_rikishi_banzuke_record(self, r: BanzukeRikishi, tournament: SumoTournament, force_update=False):
        # Check if we've seen this wrestler before
        if not r.rikishiId in self.rikishi:
            if not self._add_rikishi(r.rikishiId, r.shikonaEn, r.desc()):
                return
        # else:
        #     sys.stderr.write(f'    Found existing record for {r.desc()}{" "*40}\n')

        # Add this wrestler to the list of wrestlers in the tournament
        if not r.rikishiId in tournament.rikishi:
            tournament.rikishi.append(r.rikishiId)

        w = self.rikishi[r.rikishiId]

        #
        # Update the rikishi record with bouts-by-opponent
        # (if we don't already have it)
        #
        for record in r.record:
            # Add the opponent if we haven't seen them before
            if not record.opponentID in self.rikishi:
                if not self._add_rikishi(record.opponentID, record.opponentShikonaEn, f'{record.opponentShikonaEn}({record.opponentID})'):
                    sys.stderr.write(f'Could not add opponent ({record.opponentShikonaEn}[{record.opponentID}]) of {r.desc()}\n')
            # Add this wrestler's record vs. the opponent
            if record.opponentID > 0 and (force_update or not record.opponentID in w.matches_by_opponent):
                w.matches_by_opponent[record.opponentID] = []
                skip = 0
                limit = 1000
                while True:
                    matches, matchup = self.api.rikishi_matches(r.rikishiId, opponentId = record.opponentID, limit = limit, skip = skip)
                    for m in matches:
                        # assume the match is already in the "all_matches" list,
                        # and just keep track of the matchId here
                        w.matches_by_opponent[record.opponentID].append(m.matchId)
                    sys.stdout.write(f'    Adding wrestler:{r.desc()} +{len(matches)} matches vs. {record.opponentID}{" "*40}\r')
                    if len(matches) < limit:
                        break;
                    skip += limit

        return

    def _add_rikishi(self, rikishiId, shikonaEn, desc):
        # Create the SumoWrestler object
        # find the wrestler
        rikishi = self.api.rikishi(rikishiId, measurements=True, ranks=True, shikonas=True)
        if not rikishi:
            sys.stderr.write(f'No Rikishi data for "{desc}" from API: creating blank entry\n')
            rikishi = Rikishi(id=rikishiId, shikonaEn=shikonaEn)
            # TODO: use self.api.rikishis() and search by shikonaEn?

        sys.stdout.write(f'    Adding wrestler:{desc}...{" "*50}\n')

        # get some extra stats
        stats = self.api.rikishi_stats(rikishiId)
        if not stats:
            sys.stderr.write(f'Cannot find stats for {desc}: creating blank entry')
            stats = RikishiStats()

        all_matches = []

        # Grab _all_ matches this wrestler has ever fought
        limit = 1000
        skip = 0
        while True:
            matchlist, _ = self.api.rikishi_matches(rikishiId, limit = limit, skip = skip)
            list(map(lambda m: self._set_match(m), matchlist))
            for m in matchlist:
                all_matches.append(m.matchId)
            sys.stdout.write(f'    Adding wrestler:{desc} +{len(matchlist)} matches{" "*45}\r')
            if len(matchlist) < limit:
                break
            skip += limit

        self.rikishi[rikishiId] = SumoWrestler(rikishi, stats)
        self.rikishi[rikishiId].all_matches = all_matches

        return True

    def _add_torikumi(self, t: SumoTournament, division: SumoDivision, day):
        sys.stdout.write(f'    Add Day {day} Torikumi for {division}{" "*50}\n')

        # grab the day's torikumi in the givin division
        torikumi = self.api.basho_torikumi(t.id_str(), division, day)

        if not day in t.torikumi_by_day:
            t.torikumi_by_day[day] = {}
        if not division in t.torikumi_by_division:
            t.torikumi_by_division[division] = {}

        if torikumi:
            t.torikumi_by_day[day][division] = torikumi.torikumi
            t.torikumi_by_division[division][day] = torikumi.torikumi
            for match in torikumi.torikumi:
                if not match.eastId in self.rikishi:
                    self._add_rikishi(match.eastId, match.eastShikona, f'E:{match.eastShikona}({match.eastId})')
                if not match.westId in self.rikishi:
                    self._add_rikishi(match.westId, match.westShikona, f'W:{match.westShikona}({match.westId})')
            # Add the torikumi to the banzuke object
            # (assume the banzuke object exists)
            t.banzuke[division].add_torikumi(day, torikumi.torikumi)
        else:
            t.torikumi_by_day[day][division] = []
            t.torikumi_by_division[division][day] = []

        return

    def _set_match(self, m: BashoMatch):
        self.matches[m.matchId] = m
        return m

    def _get_match(self, mID: str):
        if mID in self.matches:
            return self.matches[mID]
        return None


