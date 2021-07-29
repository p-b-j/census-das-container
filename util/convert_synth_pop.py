import argparse
import numpy as np
import os
import pandas as pd

# Still not sure what version is used for
VERSION = 12345

def get_script_args():
    parser = argparse.ArgumentParser(
        description='Convert synthetic population file to CEF formatted person and unit files'
    )
    parser.add_argument(
        'grfc_path', 
        metavar='GRFC_PATH', 
        help='path to grfc file that will be used to run the DAS'
    )
    parser.add_argument(
        'synth_path',
        metavar='SYNTH_PATH',
        help='path to synthetic population file to convert'
    )

    return parser.parse_args()

def load_synth_df(script_args):
    grfc_path = os.path.expandvars(script_args.grfc_path)
    synth_path = os.path.expandvars(script_args.synth_path)

    synth_df = pd.read_csv(synth_path, index_col=0)

    grfc_df = pd.read_csv(
        grfc_path, 
        delimiter='|', 
        usecols=[
            'TABBLKST', 
            'TABBLKCOU',
            'TABTRACTCE',
            'TABBLKGRPCE', 
            'TABBLK', 
            'OIDTABBLK'
        ]
    )
    # Not sure if there's a better way to do this...
    grfc_df['geoid'] = (
        grfc_df['TABBLKST'].astype(str).str.zfill(2)
        + grfc_df['TABBLKCOU'].astype(str).str.zfill(3)
        + grfc_df['TABTRACTCE'].astype(str).str.zfill(6)
        + grfc_df['TABBLK'].astype(str).str.zfill(4)
    ).astype(int)

    return synth_df.join(
        grfc_df.set_index('geoid'), 
        on='geoid'
    ).dropna(subset=['OIDTABBLK']).reset_index().astype(int)

def build_per_df(synth_df, hh_gb):
    per_fields = ['RTYPE', 'MAFID', 'CUF_PNC', 'BCUSTATEFP', 'VERSION', 'QSEX', 'QAGE', 'QDB', 'QDOB_MONTH', 'QDOB_DAY', 'QDOB_YEAR', 'QSPAN', 'QSPANX', 'CENHISP', 'QRACE1', 'QRACE2', 'QRACE3', 'QRACE4', 'QRACE5', 'QRACE6', 'QRACE7', 'QRACE8', 'QRACEX', 'CENRACE', 'RACE2010', 'RELSHIP', 'QGQTYP', 'LIVE_ALONE']
    per_df = pd.DataFrame(index=np.arange(synth_df.shape[0]), columns=per_fields)

    # All housing units right now
    per_df['RTYPE'] = np.where(synth_df['relationship'].isin([16, 17]), 5, 3)
    # Need to add 100000000 to make the value valid
    # per_df['MAFID'] = str(100000000 + synth_df['hh_id'])
    per_df['MAFID'] = 100000001 + synth_df['hh_id']
    # Still don't know what this is
    per_df['CUF_PNC'] = 12345
    per_df['BCUSTATEFP'] = synth_df['state']
    # Also don't know what this is
    per_df['VERSION'] = VERSION
    per_df['QSEX'] = synth_df['sex_id']
    per_df['QAGE'] = synth_df['age']
    per_df['QDOB_YEAR'] = 2020 - synth_df['age']
    # Do we care about birth month/day?
    per_df['QDOB_MONTH'] = 1
    per_df['QDOB_DAY'] = 1
    per_df['QDB'] = (per_df['QDOB_YEAR'].astype(str) 
                        + per_df['QDOB_MONTH'].astype(str).str.zfill(2)
                        + per_df['QDOB_DAY'].astype(str).str.zfill(2))
    # Don't know exactly what the Edit/Allocation group is
    per_df['QRACEX'] = 1
    per_df['QSPANX'] = 1
    # Don't know exactly what the Q codes are
    per_df['QSPAN'] = 1000
    per_df['QRACE1'] = 1000
    per_df['QRACE2'] = 1000
    per_df['QRACE3'] = 1000
    per_df['QRACE4'] = 1000
    per_df['QRACE5'] = 1000
    per_df['QRACE6'] = 1000
    per_df['QRACE7'] = 1000
    per_df['QRACE8'] = 1000
    per_df['CENRACE'] = synth_df.apply(lambda row: get_cenrace(
        row['racsor'],
        row['racnhpi'],
        row['racasn'],
        row['racaian'],
        row['racblk'],
        row['racwht']
    ), axis=1).astype(str).str.zfill(2)
    per_df['RACE2010'] = synth_df.apply(lambda row: get_race2010(
        row['racnhpi'],
        row['racasn'],
        row['racaian'],
        row['racblk'],
        row['racwht']
    ), axis=1).astype(str).str.zfill(2)
    # For some reason CENHISP is 1 and 2 instead of 0 and 1...
    per_df['CENHISP'] = synth_df['hispanic'] + 1
    # RELSHIP range seems to be 20-38 but not documented anywhere
    per_df['RELSHIP'] = synth_df['relationship'] + 20
    # NIU but 000 isn't allowed?
    per_df['QGQTYP'] = '   '
    # Everyone living alone (for now)
    per_df['LIVE_ALONE'] = synth_df.apply(
        lambda row: 0 if hh_gb.get_group(row['hh_id']).shape[0] > 1 else 1,
        axis=1
    )
    
    return per_df

def build_unit_df(synth_df, per_df, hh_gb):
    unit_fields = ['RTYPE', 'MAFID', 'BCUSTATEFP', 'VERSION', 'FINAL_POP', 'HHLDRAGE', 'HHSPAN', 'HHLDRACE', 'HHRACE', 'TEN', 'TEN_A', 'TEN_R', 'VACS', 'QGQTYP', 'GQSEX', 'OIDTB', 'HHT', 'HHT2', 'CPLT', 'UPART', 'MULTG', 'PAOC', 'P18', 'P60', 'P65', 'P75', 'PAC', 'HHSEX']
    unit_df = pd.DataFrame(columns=unit_fields)

    for hh_id, household in hh_gb:
        new_row = {}

        head_of_household = get_head_of_household(household)

        # why don't these just match? :(
        # Should be able to subtract 1 from person RTYPE
        new_row['RTYPE'] = 4 if head_of_household['relationship'] in [16, 17] else 2
        new_row['MAFID'] = 100000001 + hh_id
        new_row['BCUSTATEFP'] = head_of_household['state'].item()
        new_row['VERSION'] = VERSION
        new_row['FINAL_POP'] = household.shape[0]
        new_row['HHLDRAGE'] = head_of_household['age'] if head_of_household['age'] >= 15 else 15
        new_row['HHSPAN'] = get_hhspan(household, new_row['RTYPE'])
        # Copying over QRACEX (CEF validator describes as "Edited QRACEX of householder")
        new_row['HHLDRACE'] = 1
        new_row['HHRACE'] = str(get_hhrace(household, new_row['RTYPE'])).zfill(2)
        # For now, we can say everyone owns free and clear?
        new_row['TEN'] = 2
        # Zero clue what these are still, we will match TEN for now
        new_row['TEN_A'] = new_row['TEN']
        new_row['TEN_R'] = new_row['TEN']
        # I think should be NIU since it's not vacant
        new_row['VACS'] = 0
        # NIU but 000 isn't allowed?
        new_row['QGQTYP'] = '   '
        # CEF Validator says "GQ Unit Sex Composition Flag"???
        new_row['GQSEX'] = ' '
        new_row['OIDTB'] = head_of_household['OIDTABBLK'].astype(np.int64).item()
        # All of these will change when we simulate households
        new_row['HHT'] = get_hht(household, new_row['RTYPE'])
        new_row['HHT2'] = str(get_hht2(household, new_row['RTYPE'])).zfill(2)
        new_row['CPLT'] = get_cplt(household, new_row['RTYPE'])
        new_row['UPART'] = get_upart(household, new_row['RTYPE'])
        new_row['MULTG'] = get_multg(household, new_row['RTYPE'])
        new_row['PAOC'] = get_paoc(household, new_row['RTYPE'])
        new_row['P18'] = get_p18(household, new_row['RTYPE'])
        new_row['P60'] = get_p60(household, new_row['RTYPE'])
        new_row['P65'] = get_p65(household, new_row['RTYPE'])
        new_row['P75'] = get_p75(household, new_row['RTYPE'])
        new_row['PAC'] = 1 if new_row['PAOC'] in [1, 2, 3] else 0
        new_row['HHSEX'] = get_hhsex(household, new_row['RTYPE'])

        unit_df = unit_df.append(new_row, ignore_index=True)

    return unit_df

def get_head_of_household(household):
    possible = household[household['relationship'].isin([0, 1, 13, 14])]
    if possible.shape[0] > 0:
        # Arbitrarily return first row
        return possible.iloc[0]
    else:
        # Arbitrarily return first row
        return household.iloc[0]

def get_hht(household, rtype):
    hhsize = household.shape[0]
    rels = household['relationship'] + 20
    rels_no_hh = rels[rels != 20]
    hhsex = get_head_of_household(household)['sex_id'].item()
    # 14 is female householder nonfamily
    if (rtype == 4) or (rtype == 2 and hhsize == 0):
        return 0
    elif (hhsize > 1) and (rels.isin([21, 23]).any()):
        return 1
    elif (hhsize > 1) and (hhsex == 1) and (rels.isin(np.arange(25, 34)).any()):
        return 2
    elif (hhsize > 1) and (hhsex == 2) and (rels.isin(np.arange(25, 34)).any()):
        return 3
    elif (hhsize == 1) and (hhsex == 1):
        return 4
    elif (hhsize > 1) and (hhsex == 1) and (rels_no_hh.isin([22, 24, 34, 35, 36]).all()):
        return 5
    elif (hhsize == 1) and (hhsex == 2):
        return 6
    elif (hhsize > 1) and (hhsex == 2) and (rels_no_hh.isin([22, 24, 34, 35, 36]).all()):
        return 7
    else:
        hh_id = household['hh_id'].iloc[0].item()
        raise ValueError(f"Could not generate hht for household w/id: {hh_id}")

def get_hht2(household, rtype):
    hhsize = household.shape[0]
    household_under_18 = household[household['age'] < 18]
    rels = household['relationship'] + 20
    rels_under_18 = household_under_18['relationship'] + 20
    hhsex = get_head_of_household(household)['sex_id'].item()
    if (rtype == 4) or (rtype == 2 and hhsize == 0):
        return 0
    elif (hhsize > 1) and (rels.isin([21, 23]).any()) and (rels_under_18.isin([25, 26, 27]).any()):
        return 1
    elif (hhsize > 1) and (rels.isin([21, 23]).any()):
        return 2
    elif (hhsize > 1) and (rels.isin([22, 24]).any()) and (rels_under_18.isin([25, 26, 27]).any()):
        return 3
    elif (hhsize > 1) and (rels.isin([22, 24]).any()):
        return 4
    elif (hhsize == 1) and (hhsex == 2):
        return 5
    elif (hhsize > 1) and (hhsex == 2) and (rels_under_18.isin([25, 26, 27]).any()):
        return 6
    elif (hhsize > 1) and (hhsex == 2) and (rels.isin(np.arange(25, 34)).any()):
        return 7
    elif (hhsize > 1) and (hhsex == 2) and (rels.isin([34, 35, 36]).any()):
        return 8
    elif (hhsize == 1) and (hhsex == 1):
        return 9
    elif (hhsize > 1) and (hhsex == 1) and (rels_under_18.isin([25, 26, 27]).any()):
        return 10
    elif (hhsize > 1) and (hhsex == 1) and (rels.isin(np.arange(25, 34)).any()):
        return 11
    elif (hhsize > 1) and (hhsex == 1) and (rels.isin([34, 35, 36]).any()):
        return 12
    else:
        hh_id = household['hh_id'].iloc[0].item()
        raise ValueError(f"Could not generate hht2 for household w/id: {hh_id}")
    
def get_cplt(household, rtype):
    hhsize = household.shape[0]
    rels = household['relationship'] + 20
    if (rtype == 4) or ((rtype == 2) and (hhsize <= 1)):
        return 0
    elif rels.isin([21]).any():
        return 1
    elif rels.isin([23]).any():
        return 2
    elif rels.isin([22]).any():
        return 3
    elif rels.isin([24]).any():
        return 4
    else:
        return 5

def get_upart(household, rtype):
    hhsize = household.shape[0]
    rels = household['relationship'] + 20
    hhsex = get_head_of_household(household)['sex_id'].item()
    sex_rels = zip(household['sex_id'], rels)
    if (rtype == 4) or (rtype == 2 and hhsize == 0):
        return 0
    elif (hhsize > 1) and (hhsex == 1) and ((1, 24) in sex_rels):
        return 1
    elif (hhsize > 1) and (hhsex == 1) and ((2, 22) in sex_rels):
        return 2
    elif (hhsize > 1) and (hhsex == 2) and ((2, 24) in sex_rels):
        return 3
    elif (hhsize > 1) and (hhsex == 2) and ((1, 22) in sex_rels):
        return 4 
    else:
        return 5

def get_multg(household, rtype):
    hhsize = household.shape[0]
    rels = household['relationship'] + 20
    if (rtype == 4) or (hhsize <= 2):
        return 0
    elif (rels.isin([25, 26, 27]).any() and rels.isin([30]).any()) or (rels.isin([29,31]).any()):
        return 2
    else:
        return 1

def get_hhldrage(household, rtype):
    hhsize = household.shape[0]
    hhage = get_head_of_household(household)['age'].item()
    if (rtype == 4) or (hhsize == 0):
        return 0
    elif (hhage < 25):
        return 1
    elif (hhage < 35):
        return 2
    elif (hhage < 45):
        return 3       
    elif (hhage < 55):
        return 4
    elif (hhage < 60):
        return 5
    elif (hhage < 65):
        return 6
    elif (hhage < 75):
        return 7
    elif (hhage < 85):
        return 8
    else:
        return 9

def get_hhspan(household, rtype):
    hhsize = household.shape[0]
    return get_head_of_household(household)['hispanic'].item() + 1
    # if (rtype == 4) or (hhsize == 0):
    #     return 0
    # else:
    #     return get_head_of_household(household)['hispanic'].item() + 1

def get_hhrace(household, rtype):
    hhsize = household.shape[0]
    householder = get_head_of_household(household)
    hhrace = get_cenrace(
        householder['racsor'].item(),
        householder['racnhpi'].item(),
        householder['racasn'].item(),
        householder['racaian'].item(),
        householder['racblk'].item(),
        householder['racwht'].item()
    )

    return hhrace

    # if (rtype == 4) or (hhsize == 0):
    #     return 0
    # elif hhrace < 7:
    #     return hhrace
    # else:
    #     return 7

def get_paoc(household, rtype):
    hhsize = household.shape[0]
    household_under_6_rels = household[household['age'] < 6]['relationship'] + 20
    household_6_to_17_rels = household[(household['age'] >= 6) & (household['age'] <= 17)]['relationship'] + 20

    children_under_6 = household_under_6_rels.isin([25, 26, 27]).any()
    children_6_to_17 = household_6_to_17_rels.isin([25, 26, 27]).any()
    if (rtype == 4) or (hhsize == 0):
        return 0
    elif hhsize > 1 and children_under_6 and not children_6_to_17:
        return 1
    elif hhsize > 1 and not children_under_6 and children_6_to_17:
        return 2
    elif hhsize > 1 and children_under_6 and children_6_to_17:
        return 3
    else:
        return 4

def get_p18(household, rtype):
    if rtype == 2 and household[household['age'] < 18].shape[0] > 0:
        return 1
    else:
        return 0

def get_p60(household, rtype):
    if rtype == 2 and household[household['age'] >= 60].shape[0] > 0:
        return 1
    else:
        return 0

def get_p65(household, rtype):
    if rtype == 2 and household[household['age'] >= 65].shape[0] > 0:
        return 1
    else:
        return 0

def get_p75(household, rtype):
    if rtype == 2 and household[household['age'] >= 75].shape[0] > 0:
        return 1
    else:
        return 0

def get_hhsex(household, rtype):
    hhsize = household.shape[0]
    if rtype == 4 or hhsize == 0:
        return 0
    else:
        return get_head_of_household(household)['sex_id'].item()


def get_cenrace(sor, nhpi, asn, aian, blk, wht):
    indicator_str = (str(int(sor))
                        + str(int(nhpi))
                        + str(int(asn))
                        + str(int(aian))
                        + str(int(blk))
                        + str(int(wht)))
    if indicator_str == '000001': return 1
    elif indicator_str == '000010': return 2
    elif indicator_str == '000100': return 3
    elif indicator_str == '001000': return 4
    elif indicator_str == '010000': return 5
    elif indicator_str == '100000': return 6
    elif indicator_str == '000011': return 7
    elif indicator_str == '000101': return 8
    elif indicator_str == '001001': return 9
    elif indicator_str == '010001': return 10
    elif indicator_str == '100001': return 11
    elif indicator_str == '000110': return 12
    elif indicator_str == '001010': return 13
    elif indicator_str == '010010': return 14
    elif indicator_str == '100010': return 15
    elif indicator_str == '001100': return 16
    elif indicator_str == '010100': return 17
    elif indicator_str == '100100': return 18
    elif indicator_str == '011000': return 19
    elif indicator_str == '101000': return 20
    elif indicator_str == '110000': return 21
    elif indicator_str == '000111': return 22
    elif indicator_str == '001011': return 23
    elif indicator_str == '010011': return 24
    elif indicator_str == '100011': return 25
    elif indicator_str == '001101': return 26
    elif indicator_str == '010101': return 27
    elif indicator_str == '100101': return 28
    elif indicator_str == '011001': return 29
    elif indicator_str == '101001': return 30
    elif indicator_str == '110001': return 31
    elif indicator_str == '001110': return 32
    elif indicator_str == '010110': return 33
    elif indicator_str == '100110': return 34
    elif indicator_str == '011010': return 35
    elif indicator_str == '101010': return 36
    elif indicator_str == '110010': return 37
    elif indicator_str == '011100': return 38
    elif indicator_str == '101100': return 39
    elif indicator_str == '110100': return 40
    elif indicator_str == '111000': return 41
    elif indicator_str == '001111': return 42
    elif indicator_str == '010111': return 43
    elif indicator_str == '100111': return 44
    elif indicator_str == '011011': return 45
    elif indicator_str == '101011': return 46
    elif indicator_str == '110011': return 47
    elif indicator_str == '011101': return 48
    elif indicator_str == '101101': return 49
    elif indicator_str == '110101': return 50
    elif indicator_str == '111001': return 51
    elif indicator_str == '011110': return 52
    elif indicator_str == '101110': return 53
    elif indicator_str == '110110': return 54
    elif indicator_str == '111010': return 55
    elif indicator_str == '111100': return 56
    elif indicator_str == '011111': return 57
    elif indicator_str == '101111': return 58
    elif indicator_str == '110111': return 59
    elif indicator_str == '111011': return 60
    elif indicator_str == '111101': return 61
    elif indicator_str == '111110': return 62
    elif indicator_str == '111111': return 63
    else: raise ValueError('Incorrect race indicator: ' + indicator_str)

def get_race2010(nhpi, asn, aian, blk, wht):
    indicator_str = (str(int(nhpi))
                        + str(int(asn))
                        + str(int(aian))
                        + str(int(blk))
                        + str(int(wht)))
    if indicator_str == '00001': return 1
    elif indicator_str == '00010': return 2
    elif indicator_str == '00100': return 3
    elif indicator_str == '01000': return 4
    elif indicator_str == '10000': return 5
    elif indicator_str == '00011': return 6
    elif indicator_str == '00101': return 7
    elif indicator_str == '01001': return 8
    elif indicator_str == '10001': return 9
    elif indicator_str == '00110': return 10
    elif indicator_str == '01010': return 11
    elif indicator_str == '10010': return 12
    elif indicator_str == '01100': return 13
    elif indicator_str == '10100': return 14
    elif indicator_str == '11000': return 15
    elif indicator_str == '00111': return 16
    elif indicator_str == '01011': return 17
    elif indicator_str == '10011': return 18
    elif indicator_str == '01101': return 19
    elif indicator_str == '10101': return 20
    elif indicator_str == '11001': return 21
    elif indicator_str == '01110': return 22
    elif indicator_str == '10110': return 23
    elif indicator_str == '11010': return 24
    elif indicator_str == '11100': return 25
    elif indicator_str == '01111': return 26
    elif indicator_str == '10111': return 27
    elif indicator_str == '11011': return 28
    elif indicator_str == '11101': return 29
    elif indicator_str == '11110': return 30
    elif indicator_str == '11111': return 31
    elif indicator_str == '00000': return 1   # This means they are SOR which wasn't part of 2010... :( 
    else: raise ValueError('Incorrect race indicator: ' + indicator_str)

def main():
    script_args = get_script_args()

    print("Loading synthetic population dataframe...")
    synth_df = load_synth_df(script_args)
    hh_gb = synth_df.groupby('hh_id')

    print("Building CEF person dataframe...")
    per_df = build_per_df(synth_df, hh_gb)

    print("Building CEF unit dataframe...")
    unit_df = build_unit_df(synth_df, per_df, hh_gb)

    print("Exporting CEF dataframes...")
    per_df.to_csv('converted_synth_pop.cef', sep='|', index=False, header=False)
    unit_df.to_csv('converted_synth_unit.cef', sep='|', index=False, header=False)
    print("Done!")

if __name__ == "__main__":
    main()
