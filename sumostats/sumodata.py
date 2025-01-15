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

    def id(self):
        return self.rikishi.id

    def shikonaEn(self):
        return self.rikishi.shikonaEn

    def __str__(self):
        return f'{self.shikonaEn()}({self.rikishi.id})'

class SumoBanzuke():
    def __init__(self, b:Banzuke):
        self.bashoId = b.bashoId
        self.division = b.division
        self.rikishi: dict[int, BanzukeRikishi] = {}

        # re-index the Banzuki records into something more easily queried
        if b.east:
            for r in b.east:
                self.rikishi[r.rikishiId] = r
        if b.west:
            for r in b.west:
                self.rikishi[r.rikishiId] = r
        return

    def get_record(self, rID):
        if not rID in self.rikishi:
            return None
        return self.rikishi[rID]

class SumoTournament():
    def __init__(self, b:Basho):
        self.basho: Basho = b
        self.rikishi: list[int] = []
        self.banzuke: dict[SumoDivision, SumoBanzuke] = {}

        # TODO: de-dup the BashoTorikumi for lower memory usage when un-pickling?

        # The Torikumi is the list of matches (and results)
        self.torikumi_by_division: dict[SumoDivision, dict[int, BashoTorikumi]] = {}
        self.torikumi_by_day: dict[int, dict[SumoDivision, BashoTorikumi]] = {}
        return

    def id(self):
        return self.basho.id()

    def get_rikishi_record(self, rID: int):
        if not rID in self.rikishi:
            return None, None

        # the rikishi fought in this tournament - look through the banzuke to
        # find their record
        for div in (SumoDivision):
            if div.value in self.banzuke:
                r = self.banzuke[div.value].get_record(rID)
                if r:
                    return r, div.value

        sys.stderr.write(f'LookupError: did not find rID:{rID} in any division in {self.id()} (but they competed?)\n')
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

    def get_rikishi(self, rikishiId):
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

    def get_matchup_record(self, rikishi:int, opponent:int):
        """
        Create a RikishiMatchup object for all bouts between the specified rikishi and opponent
        """
        if not rikishi in self.rikishi:
            return None
        matchlist = self.rikishi[rikishi].matches_by_opponent[opponent]
        if not matchlist:
            return None

        matchup = RikishiMatchup()
        matchup.total = len(matchlist)
        matchup.matches = list(map(lambda m: self.matches.get(m), matchlist))
        for m in matchup.matches:
            if m.winnerId == rikishi:
                matchup.rikishiWins += 1
                if not m.kimarite in matchup.kimariteWins:
                    matchup.kimariteWins[m.kimarite] = 0
                matchup.kimariteWins[m.kimarite] += 1
            else:
                matchup.opponentWins += 1
                if not m.kimarite in matchup.kimariteLosses:
                    matchup.kimariteLosses[m.kimarite] = 0
                matchup.kimariteLosses[m.kimarite] += 1
        return matchup

    def get_rikishi_basho_record(self, rikishiId, basho):
        """
        Get the record of a rikishi in a specific basho.
        Returns a pair: list[BanzukeRikishi], SumoDivision
        """
        if not rikishiId in self.rikishi:
            return [], SumoDivision.Unknown

        bashoDate = BashoDate(basho)
        if not bashoDate in self.basho:
            return [], SumoDivision.Unknown

        return self.basho[bashoDate].get_rikishi_record(rikishiId)

    def get_rikishi_basho_record_by_day(self, rikishiId, basho, day):
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
            sys.stderr.write(f'Could not query basho:{bashoId}\n')
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
    Private Methods

    """

    def _add_basho(self, b: Basho, division: SumoDivision, forceUpdate = False):
        if not b or not b.isValid():
            return

        tournament = None
        if b.bashoDate in self.basho:
            # Assume we already know about this one
            if not forceUpdate:
                sys.stderr.write(f'Skipping tournament: {b.id()} (already in table)\n')
                return
            sys.stderr.write(f'Updating tournament: {b.id()} (from API source)\n')
            tournament = self.basho[b.bashoDate]
            tournament.basho = b
        else:
            sys.stdout.write(f'Add New SumoTournament: {b.id()}\n')
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
        sys.stdout.write(f'Query Banzuke for {division} (in {tournament.id()})\n')
        # Use the API to grab banzuke info
        banzuke = self.api.basho_banzuke(tournament.id(), division)
        if not banzuke:
            sys.stderr.write(f'    ERROR: No {division} banzuke found for basho:{tournament.id()}')
            return

        # Updates will just replace the banzuke
        tournament.banzuke[division] = SumoBanzuke(banzuke)

        max_bouts = 0

        # iterate over banzuke Rikishi
        if banzuke.east:
            for rikishi in banzuke.east:
                self._add_rikishi_banzuke_record(rikishi, tournament, forceUpdate)
                bouts = rikishi.wins + rikishi.losses + rikishi.absences
                if bouts > max_bouts:
                    max_bouts = bouts
        else:
            sys.stderr.write(f'No east side in banzuke:{banzuke}\n')

        if banzuke.west:
            for rikishi in banzuke.west:
                self._add_rikishi_banzuke_record(rikishi, tournament, forceUpdate)
                bouts = rikishi.wins + rikishi.losses + rikishi.absences
                if bouts > max_bouts:
                    max_bouts = bouts
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
        #     sys.stderr.write(f'    Found existing record for {r.desc()}\n')

        # Add this wrestler to the list of wrestlers in the tournament
        if not r.rikishiId in tournament.rikishi:
            tournament.rikishi.append(r.rikishiId)

        w = self.rikishi[r.rikishiId]

        #
        # Update the rikishi record with bouts-by-opponent
        # (if we don't already have it)
        #
        skip = 0
        limit = 1000
        for record in r.record:
            # Add this wrestler's record vs. the opponent
            if record.opponentID > 0 and (force_update or not record.opponentID in w.matches_by_opponent):
                w.matches_by_opponent[record.opponentID] = []
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
        rikishi = self.api.rikishi(rikishiId, measurements=True, ranks=True)
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
        self.rikishi[rikishiId].matches = all_matches

        return True

    def _add_torikumi(self, t: SumoTournament, division: SumoDivision, day):
        sys.stdout.write(f'    Add Day {day} Torikumi for {division}{" "*50}\n')

        # grab the day's torikumi in the givin division
        torikumi = self.api.basho_torikumi(t.id(), division, day)

        if not day in t.torikumi_by_day:
            t.torikumi_by_day[day] = {}
        if not division in t.torikumi_by_division:
            t.torikumi_by_division[division] = {}

        t.torikumi_by_day[day][division] = torikumi
        t.torikumi_by_division[division][day] = torikumi
        return

    def _set_match(self, m: BashoMatch):
        self.matches[m.matchId] = m
        return m

    def _get_match(self, mID: str):
        if mID in self.matches:
            return self.matches[mID]
        return None


