#!/usr/bin/env python3

from .sumoapi import *
from datetime import date
import pickle

class SumoWrestler():
    def __init__(self, r: Rikishi, s: RikishiStats):
        self.rikishi: Rikishi = r
        self.stats: RikishiStats = s
        self.all_matches: list[BashoMatch] = []
        self.matches_by_opponent: dict[int, list[BashoMatch]] = {}
        return

    def id(self):
        return self.rikishi.id

class SumoTournament():
    def __init__(self, b:Basho):
        self.basho: Basho = b
        self.rikishi: list[int] = []
        self.banzuke: dict[SumoDivision, Banzuke] = {}
        self.torikumi_by_division: dict[SumoDivision, dict[int, BashoTorikumi]] = {}
        self.torikumi_by_day: dict[int, dict[SumoDivision, BashoTorikumi]] = {}
        return

    def id(self):
        return BashoIdStr(self.basho.bashoDate)

class SumoTable:
    """ Build a database of sumo wrestlers and match """

    def __init__(self):
        self.api = SumoAPI()
        self.rikishi: dict[int, SumoWrestler] = {}
        self.basho: dict[date, SumoTournament] = {}
        self.matches: dict[str, BashoMatch] = {}
        return

    def load_table(path):
        """ Load a SumoTable from a file """
        f = file.open(path, 'rb')
        try:
            table = pickle.load(f)
        except:
            table = None
        f.close()
        if not isinstance(table, SumoTable):
            raise Exception(f'Invalid saved table file at {path}: not a SumoTable')
        return table

    def save_table(self, path):
        """ Save SumoTable instance to a file """
        f = file.open(path, 'wb')
        pickle.dump(self, f)
        f.close()
        return

    def build_table_from_dates(self, startDate: date, endDate: date, division: SumoDivision = SumoDivision.UNKNOWN):
        # Iterate through the specified dates finding all Basho (in the division)
        return

    def TEST_IT(self):
        print("basho = self.api.basho('202411')")
        basho = self.api.basho('202411')
        self._add_basho(basho, SumoDivision.UNKNOWN)
        return

    def _add_basho(self, b: Basho, division: SumoDivision):
        if not b or not b.isValid():
            return
        if b.bashoDate in self.basho:
            # Assume we already know about this one
            return

        print(f'new SumoTournament: {BashoIdStr(b.bashoDate)}')
        # Add this basho to our table as a set of Tournament objects
        tournament = SumoTournament(b)

        # retrieve the set of banzuke for this basho
        if division == SumoDivision.UNKNOWN:
            for div in (SumoDivision):
                self._add_banzuke(tournament, div.value)
        else:
            self._add_banzuke(tournament, division)

        # add the tournament to our table
        self.basho[b.bashoDate] = tournament
        return

    def _add_banzuke(self, tournament: SumoTournament, division: SumoDivision):
        print(f'New Banzuke for {division}')
        # Use the API to grab banzuke info
        banzuke = self.api.basho_banzuke(tournament.id(), division)

        max_bouts = 0

        # iterate over banzuke Rikishi
        for rikishi in banzuke.east:
            self._add_rikishi_banzuke_record(rikishi)
            bouts = rikishi.wins + rikishi.losses + rikishi.absences
            if bouts > max_bouts:
                max_bouts = bouts

        for rikishi in banzuke.west:
            self._add_rikishi_banzuke_record(rikishi)
            bouts = rikishi.wins + rikishi.losses + rikishi.absences
            if bouts > max_bouts:
                max_bouts = bouts

        # For each day of the tournament, add the torikumi
        for day in range(1, max_bouts+1):
            self._add_torikumi(tournament, division, day)

        tournament.banzuke[division] = banzuke
        return

    def _add_rikishi_banzuke_record(self, r: BanzukeRikishi):
        if r.rikishiId in self.rikishi:
            # Assume we've already seen this wrestler
            return

        print(f'    Adding wrestler:{r.rikishiId}')
        # find the wrestler
        rikishi = self.api.rikishi(r.rikishiId, measurements=True, ranks=True)
        if not rikishi:
            print(f'No Rikishi data for "{r.shikonaEn}" ID:{r.rikishiId}')
            # TODO: use self.api.rikishis() and search by shikonaEn?
            return

        # get some extra stats
        stats = self.api.rikishi_stats(r.rikishiId)

        w = SumoWrestler(rikishi, stats)

        # Add bouts-by-opponent if we don't already have it
        skip = 0
        limit = 1000
        for record in r.record:
            # Add this wrestler's record vs. the opponent
            if record.opponentID > 0 and not record.opponentID in w.matches_by_opponent:
                w.matches_by_opponent[record.opponentID] = []
                while True:
                    matches = self.api.rikishi_matches(r.rikishiId, opponentId = record.opponentID, limit = limit, skip = skip)
                    w.matches_by_opponent[record.opponentID].append(matches)
                    print(f'        +{len(matches)} matches vs. {record.opponentID}')
                    if len(matches) < limit:
                        break;
                    skip += limit

        # Grab _all_ matches this wrestler has ever fought
        limit = 1000
        skip = 0
        while True:
            matches = self.api.rikishi_matches(r.rikishiId, limit = limit, skip = skip)
            w.all_matches.append(matches)
            print(f'        +{len(matches)} matches')
            if len(matches) < limit:
                break
            skip += limit

        #
        # TODO: for each match we just found, add it to our global table: self.matches
        #
        self.rikishi[r.rikishiId] = w
        return

    def _add_torikumi(self, t: SumoTournament, division: SumoDivision, day):
        print(f'    Add Day {day} Torikumi for {division}')

        # grab the day's torikumi in the givin division
        torikumi = self.api.basho_torikumi(t.id(), division, day)

        if not day in t.torikumi_by_day:
            t.torikumi_by_day[day] = {}
        if not division in t.torikumi_by_division:
            t.torikumi_by_division[division] = {}

        t.torikumi_by_day[day][division] = torikumi
        t.torikumi_by_division[division][day] = torikumi
        return

    def _add_match(self, BashMatch):
        return

