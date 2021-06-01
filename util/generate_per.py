import pandas as pd

per_fields = ['RTYPE', 'MAFID', 'CUF_PNC', 'BCUSTATEFP', 'VERSION', 'QSEX', 'QAGE', 'QDB', 'QDOB_MONTH', 'QDOB_DAY', 'QDOB_YEAR', 'QSPAN', 'QSPANX', 'CENHISP', 'QRACE1', 'QRACE2', 'QRACE3', 'QRACE4', 'QRACE5', 'QRACE6', 'QRACE7', 'QRACE8', 'QRACEX', 'CENRACE', 'RACE2010', 'RELSHIP', 'QGQTYP', 'LIVE_ALONE']
per_df = pd.DataFrame(columns=per_fields)

new_row_template = {
    "RTYPE"         : '3',
    "MAFID"         : '899999999',
    "CUF_PNC"       : '12345',
    "BCUSTATEFP"    : '53',
    "VERSION"       : '12345',
    "QSEX"          : '1',
    "QAGE"          : '25',
    "QDB"           : '19960101',
    "QDOB_MONTH"    : '1',
    "QDOB_DAY"      : '1',
    "QDOB_YEAR"     : '1996',
    "QSPAN"         : '1000',
    "QSPANX"        : '1',
    "CENHISP"       : '1',
    "QRACE1"        : '1000',
    "QRACE2"        : '1000',
    "QRACE3"        : '1000',
    "QRACE4"        : '1000',
    "QRACE5"        : '1000',
    "QRACE6"        : '1000',
    "QRACE7"        : '1000',
    "QRACE8"        : '1000',
    "QRACEX"        : '1',
    "CENRACE"       : '11',
    "RACE2010"      : '11',
    "RELSHIP"       : '21',
    "QGQTYP"        : '   ',
    "LIVE_ALONE"    : '0',
}

for age in [25, 26, 27, 28]:
    new_row_template["CUF_PNC"] = '123' + str(age)
    new_row_template["QAGE"] = str(age)
    birthyear = 2021 - age
    new_row_template["QDB"] = str(birthyear) + '0101'
    new_row_template["QDOB_YEAR"] = str(birthyear)
    if age != 28:
        new_row_template["RELSHIP"] = '35'

    per_df = per_df.append(new_row_template, ignore_index=True)

per_df.to_csv('seattle_arboretum_per.cef', sep='|', index=False)