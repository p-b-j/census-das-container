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

def build_per_df(synth_df):
    per_fields = ['RTYPE', 'MAFID', 'CUF_PNC', 'BCUSTATEFP', 'VERSION', 'QSEX', 'QAGE', 'QDB', 'QDOB_MONTH', 'QDOB_DAY', 'QDOB_YEAR', 'QSPAN', 'QSPANX', 'CENHISP', 'QRACE1', 'QRACE2', 'QRACE3', 'QRACE4', 'QRACE5', 'QRACE6', 'QRACE7', 'QRACE8', 'QRACEX', 'CENRACE', 'RACE2010', 'RELSHIP', 'QGQTYP', 'LIVE_ALONE']
    per_df = pd.DataFrame(index=np.arange(synth_df.shape[0]), columns=per_fields)

    # All housing units right now
    per_df['RTYPE'] = 3
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
    # Not sure exactly what this is but copying CENRACE for now
    per_df['RACE2010'] = per_df['CENRACE']
    # For some reason CENHISP is 1 and 2 instead of 0 and 1...
    per_df['CENHISP'] = synth_df['hispanic'] + 1
    # RELSHIP range seems to be 20-38 but not documented anywhere
    per_df['RELSHIP'] = synth_df['relationship'] + 20
    # NIU but 000 isn't allowed?
    per_df['QGQTYP'] = '   '
    # Everyone living alone (for now)
    per_df['LIVE_ALONE'] = 1
    
    return per_df

def build_unit_df(synth_df, per_df):
    unit_fields = ['RTYPE', 'MAFID', 'BCUSTATEFP', 'VERSION', 'FINAL_POP', 'HHLDRAGE', 'HHSPAN', 'HHLDRACE', 'HHRACE', 'TEN', 'TEN_A', 'TEN_R', 'VACS', 'QGQTYP', 'GQSEX', 'OIDTB', 'HHT', 'HHT2', 'CPLT', 'UPART', 'MULTG', 'PAOC', 'P18', 'P60', 'P65', 'P75', 'PAC', 'HHSEX']
    unit_df = pd.DataFrame(index=np.arange(synth_df.shape[0]), columns=unit_fields)

    # why don't these just match? :(
    # Should be able to subtract 1 from person RTYPE
    unit_df['RTYPE'] = per_df['RTYPE'] - 1
    # Just match each of the rows since we are doing 1 person per house
    unit_df['MAFID'] = per_df['MAFID']
    unit_df['BCUSTATEFP'] = per_df['BCUSTATEFP']
    unit_df['VERSION'] = VERSION
    unit_df['FINAL_POP'] = 1
    unit_df['HHLDRAGE'] = np.where(per_df['QAGE'] >= 15, per_df['QAGE'], 15)
    unit_df['HHSPAN'] = per_df['CENHISP']
    # Copying over QRACEX (CEF validator describes as "Edited QRACEX of householder")
    unit_df['HHLDRACE'] = per_df['QRACEX']
    unit_df['HHRACE'] = per_df['CENRACE']
    # For now, we can say everyone owns free and clear?
    unit_df['TEN'] = 2
    # Zero clue what these are still, we will match TEN for now
    unit_df['TEN_A'] = unit_df['TEN']
    unit_df['TEN_R'] = unit_df['TEN']
    # I think should be NIU since it's not vacant
    unit_df['VACS'] = 0
    # NIU but 000 isn't allowed?
    unit_df['QGQTYP'] = '   '
    # CEF Validator says "GQ Unit Sex Composition Flag"???
    unit_df['GQSEX'] = ' '
    unit_df['OIDTB'] = synth_df['OIDTABBLK'].astype(np.int64)
    # All of these will change when we simulate households
    unit_df['HHT'] = np.where(per_df['QSEX'], 4, 6)
    unit_df['HHT2'] = np.char.zfill(np.where(per_df['QSEX'], 9, 5).astype(str), 2)
    unit_df['CPLT'] = 0
    unit_df['UPART'] = 0
    unit_df['MULTG'] = 1
    unit_df['PAOC'] = np.where(per_df['QAGE'] < 18, 1, 0)
    unit_df['P18'] = np.where(per_df['QAGE'] < 18, 1, 0)
    unit_df['P60'] = np.where(per_df['QAGE'] >= 60, 1, 0)
    unit_df['P65'] = np.where(per_df['QAGE'] >= 65, 1, 0)
    unit_df['P75'] = np.where(per_df['QAGE'] >= 75, 1, 0)
    unit_df['PAC'] = np.where(per_df['QAGE'] < 18, 1, 0)
    unit_df['HHSEX'] = per_df['QSEX']

    return unit_df

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

def main():
    script_args = get_script_args()

    print("Loading synthetic population dataframe...")
    synth_df = load_synth_df(script_args)

    print("Building CEF person dataframe...")
    per_df = build_per_df(synth_df)

    print("Building CEF unit dataframe...")
    unit_df = build_unit_df(synth_df, per_df)

    print("Exporting CEF dataframes...")
    per_df.to_csv('converted_synth_pop.cef', sep='|', index=False, header=False)
    unit_df.to_csv('converted_synth_unit.cef', sep='|', index=False, header=False)
    print("Done!")

if __name__ == "__main__":
    main()
