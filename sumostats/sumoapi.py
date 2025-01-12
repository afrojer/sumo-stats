#!/usr/bin/env python3

import httpx
import sys
from .sumoclasses import *

class SumoAPI:
    """ Object wrapper around sumo-api.com API calls """

    def __init__(self):
        self.apiurl = "https://sumo-api.com/api"

    def _get_json(self, url, params):
        r = None
        try:
            # do the API call, catch errors 
            r = httpx.get(url, params=params).raise_for_status()
        except httpx.RequestError as exc:
            sys.stderr.write(f'An error occurred while requesting {exc.request.url!r}.\n')
            return None
        except httpx.HTTPStatusError as exc:
            sys.stderr.write(f'Error response {exc.response.status_code} while requesting {exc.request.url!r}.\n')
            return None

        # check to see if this is valid json (takes at least 2 bytes)
        if r.status_code == 204 or len(r.text) < 2:
            return None
        return r.json()

    def rikishis(self, limit = 1000, skip = 0, retired = False, **query):
        """ GET /rikishis """
        url = self.apiurl + "/rikishis"
        # shikonaEn: search for a rikishi by English shikona
        # heya: search by heya, full name in English, e.g. Isegahama
        # sumodbId: search by sumoDB ID, e.g. 11927 = Terunofuji
        # nskId: search by official NSK ID, e.g. 3321 = Terunofuji
        # intai: (retirement date) if missing, only active rikishi are searched. If true, retired rikishi are also searched.
        # measurements: if true, the changes in a rikishi's measurements over time will be included in the response
        # ranks: if true, the changes in a rikishi's ranks over time will be included in the response
        # shikonas: if true, the changes in a rikishi's shikonas over time will be included in the response
        # limit: how many results to return, 1000 hard limit
        # skip: skip over the number of results specified
        validparams = ['shikonaEn', 'heya', 'sumodbId', 'nskId', 'measurements', 'ranks', 'shikonas']
        params = { 'limit': limit, 'skip': skip, 'intai': 'true' if retired else 'false' }
        for name, val in query.items():
            if name in validparams:
                params[name] = val
            else:
                raise Exception('invalid parameter:', name)

        j = self._get_json(url, params)
        if not j or not "total" in j or j["total"] < 1:
            sys.stderr.write(f'Could not find rikishi from query parameters: {query}\n')
            return []
        if not "records" in j:
            sys.stderr.write(f'"records" not in json response"\n{j}\n')
            return []
        # print(j)
        return list(map(Rikishi.from_dict, j["records"]))

    def rikishi(self, rikishiId, measurements = False, ranks = False, shikonas = False):
        """ GET /api/rikishi/:rikishiId """
        url = self.apiurl + f'/rikishi/{rikishiId}'
        # measurements: if true, the changes in a rikishi's measurements over time will be included in the response
        # ranks: if true, the changes in a rikishi's ranks over time will be included in the response
        # shikonas: if true, the changes in a rikishi's shikonas over time will be included in the response
        params = {}
        if measurements:
            params['measurements']='true'
        if ranks:
            params['ranks']='true'
        if shikonas:
            params['shikonas']='true'

        j = self._get_json(url, params)
        if not j:
            return None
        # print(j)
        return Rikishi.from_dict(j)

    def rikishi_stats(self, rikishiId):
        """ GET /api/rikishi/:rikishiId/stats """
        url = self.apiurl + f'/rikishi/{rikishiId}/stats'
        j = self._get_json(url, {})
        if not j:
            return None
        # print(j)
        return RikishiStats.from_dict(j)

    def rikishi_matches(self, rikishiId, bashoId = None, opponentId = None, limit = 0, skip = 0):
        """
        GET /api/rikishi/:rikishiId/matches
        GET /api/rikishi/:rikishiId/matches/:opponentId
        """
        url = self.apiurl + f'/rikishi/{rikishiId}/matches'
        params={ 'limit': limit, 'skip': skip }
        if bashoId:
            params["bashoId"] = bashoId
        if opponentId:
            url += f'/{int(opponentId)}'
        # print(url, params)
        j = self._get_json(url, params)
        if not j or not "total" in j or j["total"] < 1:
            sys.stderr.write(f'Could not find Rikishi matches for R:{rikishiId} (basho:{bashoId}, opponent:{opponentId})\n')
            # sys.stderr.write(f'{j}\n')
            return [], None
        # print(j)
        if opponentId:
            matchup = RikishiMatchup.from_dict(j)
            return matchup.matches, matchup
        else:
            return list(map(BashoMatch.from_dict, j["records"])), None

    def basho(self, bashoId):
        """ GET /api/basho/:bashoId """
        url = self.apiurl + f'/basho/{bashoId}'
        j = self._get_json(url, {})
        if not j or not "date" in j:
            sys.stderr.write(f'Could not find basho:{bashoId}\n')
            # sys.stderr.write(f'{j}\n')
            return None
        # print(j)
        return Basho.from_dict(j)

    def basho_banzuke(self, bashoId, division: SumoDivision):
        """ GET /api/basho/:bashoId/banzuke/:division """
        url = self.apiurl + f'/basho/{bashoId}/banzuke/{division}'
        j = self._get_json(url, {})
        if not j or not "bashoId" in j:
            sys.stderr.write(f'Could not find banzuke for basho:{bashoId}\n')
            # sys.stderr.write(f'{j}\n')
            return None
        # print(j)
        return Banzuke.from_dict(j)

    def basho_torikumi(self, bashoId, division: SumoDivision, day: int):
        """ GET /api/basho/:bashoId/torikumi/:division/:day """
        url = self.apiurl + f'/basho/{bashoId}/torikumi/{division}/{day}'
        j = self._get_json(url, {})
        if not j or not "torikumi" in j:
            sys.stderr.write(f'Could not find torikumi for basho:{bashoId}\n')
            # sys.stderr.write(f'{j}\n')
            return None
        # print(j)
        t = BashoTorikumi.from_dict(j)
        t.division = division
        t.day = day
        return t



#GET /api/kimarite
#GET /api/kimarite/:kimarite

#GET /api/measurements
#GET /api/ranks
#GET /api/shikonas
