import pandas as pd

unit_fields = ['RTYPE', 'MAFID', 'BCUSTATEFP', 'VERSION', 'FINAL_POP', 'HHLDRAGE', 'HHSPAN', 'HHLDRACE', 'HHRACE', 'TEN', 'TEN_A', 'TEN_R', 'VACS', 'QGQTYP', 'GQSEX', 'OIDTB', 'HHT', 'HHT2', 'CPLT', 'UPART', 'MULTG', 'PAOC', 'P18', 'P60', 'P65', 'P75', 'PAC', 'HHSEX']

unit_df = pd.DataFrame(columns=unit_fields)

new_row = {
    "RTYPE"         : '2',
    "MAFID"         : '899999999',
    "BCUSTATEFP"    : '53',
    "VERSION"       : '12345',
    "FINAL_POP"     : '4',
    "HHLDRAGE"      : '25',
    "HHSPAN"        : '1',
    "HHLDRACE"      : '1',
    "HHRACE"        : '11',
    "TEN"           : '2',
    "TEN_A"         : '2',
    "TEN_R"         : '2',
    "VACS"          : '0',
    "QGQTYP"        : '   ',
    "GQSEX"         : '1',
    "OIDTB"         : '27659836057514',
    "HHT"           : '5',
    "HHT2"          : '12',
    "CPLT"          : '0',
    "UPART"         : '0',
    "MULTG"         : '1',
    "PAOC"          : '4',
    "P18"           : '0',
    "P60"           : '0',
    "P65"           : '0',
    "P75"           : '0',
    "PAC"           : '4',
    "HHSEX"         : '1',
}

unit_df = unit_df.append(new_row, ignore_index=True)

unit_df.to_csv('seattle_arboretum_unit.cef', sep='|', index=False)
