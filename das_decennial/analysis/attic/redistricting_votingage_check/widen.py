"""
2019.06.28

File for Tommy - He wanted me to replicate the Voting Age Total mistake and demonstrate that it was just due to
a calculation/numpy indexing error.

This takes the RI Redistricting Experiment data (at PLB = 0.25) across the 3 runs Tommy specified that he
showed DOJ.
"""

import pandas
import das_utils as du
from programs.schema.schemas.schemamaker import SchemaMaker
import numpy

paths = [
    "/mnt/users/moran331/redistricting/agecat_redistricting_state_totals_2019_06_27/td025_1/agecat_all_25_runs.csv"
]
df = pandas.read_csv(paths[0])
df = df[df.columns[1:]]

wide = {}
run_ids = df.run_id.unique().tolist()
keep_run_ids = { "run_6": "DA-Run A", "run_17": "DA-Run B", "run_23": "DA-Run C" }
run_ids.sort(key=lambda s: int(s.split("_")[1]))
for r, run_id in enumerate(run_ids):
    if r == 0:
        wide['State'] = df[df['run_id'] == run_id].reset_index()['State']
        wide['plb'] = df[df['run_id'] == run_id].reset_index()['plb']
        wide['agecat'] = df[df['run_id'] == run_id].reset_index()['agecat']
        wide['orig'] = df[df['run_id'] == run_id].reset_index()['orig']
    wide[run_id] = df[df['run_id'] == run_id].reset_index()['priv']
# 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production

widedf = pandas.DataFrame(wide)

schema = SchemaMaker.fromName(name="PL94_P12")
levels = schema.levels['agecat']

widedf['agecat'] = pandas.Categorical(widedf['agecat'], categories=levels)
widedf = widedf.sort_values('agecat')
widedf = widedf[['State', 'plb', 'agecat', 'orig'] + [f"run_{i}" for i in range(25)]]
widedf = widedf.reset_index()
widedf = widedf[widedf.columns[1:]]

widedf = widedf[["State", "plb", "agecat", "orig"] + list(keep_run_ids.keys())]
widedf = widedf.rename(columns=keep_run_ids)

va_ind = numpy.array(schema.getQuerySeed("voting").groupings['agecat']).flatten().tolist()

incorrect_va_ind = numpy.array(schema.getQuerySeed("voting").groupings['agecat']).flatten().tolist()[:-1]

nva_ind = numpy.array(schema.getQuerySeed("nonvoting").groupings['agecat']).flatten().tolist()

va_df = widedf.iloc[va_ind]
incorrect_va_df = widedf.iloc[incorrect_va_ind]
nva_df = widedf.iloc[nva_ind]

vals = list(keep_run_ids.values()) + ['orig']
totals = pandas.DataFrame(widedf[vals].sum(axis=0)).unstack().unstack()
va_totals = pandas.DataFrame(va_df[vals].sum(axis=0)).unstack().unstack()
incorrect_va_totals = pandas.DataFrame(incorrect_va_df[vals].sum(axis=0)).unstack().unstack()
nva_totals = pandas.DataFrame(nva_df[vals].sum(axis=0)).unstack().unstack()

for df in [totals, va_totals, incorrect_va_totals, nva_totals]:
    df['State'] = "44"
    df['plb'] = "0.25"

totals['agecat'] = "Population Total"
va_totals['agecat'] = "Voting Age Total"
nva_totals['agecat'] = "Non-Voting Age Total"
incorrect_va_totals['agecat'] = "Voting Age Total (missing '85 years and over')"

widedf = pandas.concat([widedf, incorrect_va_totals, va_totals, nva_totals, totals])
widedf = widedf[["State", "plb", "agecat", "orig", "DA-Run A", "DA-Run B", "DA-Run C"]]
widedf.to_csv("/mnt/users/moran331/redistricting/agecat_redistricting_state_totals_2019_06_27/agecat_DOJ_runs.csv", index=False)
