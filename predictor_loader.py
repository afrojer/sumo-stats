#!/usr/bin/env python3
#
# predictor_loader.py
#
# TODO: I think this should actually be part of sumostats/sumocalc.py
#       but that means moving all the comparisons into the package as well
#
#       maybe that's ok with the predictor object can be instantiated with
#       just a json config file?
#

import os
import sys
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)

from sumostats.sumocalc import *

# We need to explicitly import all possible comparators so we have their class
# names in this script's globals() list
#
from compare_physical import *
from compare_record import *

class SumoBoutPredictorLoader:
    """
    This class loads and saves a SumoBoutPredictor instance based on a json config file.
    The jason config should look roughly like this:
    {
        "comparisons": {
            "CompareClass1": { "weight": <float>,
                               "by_day": { "1": <float>, "2": <float> ...},
                               "by_month": { "01": <float>, "03": <float> ...}
            },
            "CompareClass2": ...
        }
    }
    """

    # static method to create an instance from a json config file
    def from_json(filename:str, data:SumoData) -> SumoBoutPredictor:
        jobj = None
        try:
            with open(filename, 'r') as jsonfile:
                jobj = json.load(jsonfile)
            jsonfile.close()
        except:
            sys.stderr.write(f'Could not load prediction config file "{filename}"\n')
        if not jobj:
            return None

        if not "comparisons" in jobj:
            sys.stderr.write(f'Could not file "comparisons" in {filename}\n')
            return None

        cdict = jobj["comparisons"]
        if not isinstance(cdict, dict):
            return None

        clist:list[SumoBoutCompare] = []
        for k, v in cdict.items():
            if not isinstance(v, dict):
                sys.stderr.write(f'comparator "{k}" is not a dictionary\n')
                return None
            # look for overall weight
            if not "weight" in v:
                sys.stderr.write(f'comparator "{k}" does not contain "weight"\n')
                return None
            weight = float(v["weight"])

            # look for confidence values
            correct_confidence = 0.0
            if "correct_confidence" in v:
                correct_confidence = float(v["correct_confidence"])
            wrong_confidence = 0.0
            if "wrong_confidence" in v:
                wrong_confidence = float(v["wrong_confidence"])

            # now look for weight by basho day
            by_day = {}
            if "by_day" in v and isinstance(v["by_day"], dict):
                for d, w in v["by_day"].items():
                    if isinstance(w, list) and len(w) > 1:
                        by_day[int(d)] = w
                    else:
                        sys.stderr.write(f'Not loading day{d} in {k}: value is not a list > 1\n')

            # now look for weight by basho month
            by_month = {}
            if "by_month" in v and isinstance(v["by_month"], dict):
                for m, w in v["by_month"].items():
                    if isinstance(w, list) and len(w) > 1:
                        by_month[int(m)] = w
                    else:
                        sys.stderr.write(f'Not loading month {m} in {k}: value is not a list > 1\n')
            # the 'k' is the name of a class - check to see if we have one
            if not str(k) in globals():
                sys.stderr.write(f'Cannot find SumoBoutCompare class "{k}"\n')
                sys.stderr.write(f'\n{globals()}\n\n')
                return None
            # instantiate the class
            clist.append(globals()[k](data, weight=weight, \
                                      correct_confidence=correct_confidence, \
                                      wrong_confidence=wrong_confidence, \
                                      weight_by_day=by_day, weight_by_month=by_month))
        return SumoBoutPredictor(data, clist)

    # Save bout predictor to a config file
    def to_json(predictor:SumoBoutPredictor) -> str:
        pdict = predictor.construct_suggested_weights()
        jdict = { "comparisons": pdict }
        return json.dumps(jdict, indent=4)

    def save_json(predictor:SumoBoutPredictor, filename:str) -> None:
        with open(filename, "w") as outfile:
            outfile.write(SumoBoutPredictorLoader.to_json(predictor))
        return
