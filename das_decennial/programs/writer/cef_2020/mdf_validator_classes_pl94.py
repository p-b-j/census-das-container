#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file was automatically generated by census_etl/spec_scanner.py on Thu Sep 24 09:39:22 2020
# Command line: census_etl/spec_scanner.py mdf/2020 Public Law 94 171 Microdata Detail File Specification v2_delivered 09222020.docx --output_parser mdf_validator_classes.py --tablenames MDF_Person MDF_Unit

# Automatically generated on Thu Sep 24 09:39:22 2020 by C:\cygwin64\home\will0555\micah\etl_2020\ctools\schema\table.py

def leftpad(x,width):
    return '0'*(width-len(str(x)))+str(x)

def between(a,b,c,width):
    if len(b) > width:
        return False
    if '.' in a or '.' in b or '.' in c:
        try:
            return float(a) <= float(b) <= float(c)
        except ValueError:
            pass  # tries to return a float but might have weird input like 1.1.0 which will be compared traditionally instead
    b = b.replace(' ', '0')
    return leftpad(a,width) <= leftpad(b,width) <= leftpad(c,width)


def safe_int(i):
    try:
        return int(i)
    except (TypeError, ValueError) as e:
        return None

def safe_float(i):
    try:
        return float(i)
    except (TypeError, ValueError) as e:
        return None

def safe_str(i):
    try:
        return str(i)
    except (TypeError, ValueError) as e:
        return None


class MDF_Person_validator:
    @classmethod
    def is_valid_SCHEMA_TYPE_CODE(self,x):
        """Schema Type Code"""
        if x is None or x == "None":
            return False
        return (leftpad(x,3)==leftpad('MPD',3))
    @classmethod
    def is_valid_SCHEMA_BUILD_ID(self,x):
        """Schema Build ID"""
        if x is None or x == "None":
            return False
        return True
    @classmethod
    def is_valid_TABBLKST(self,x):
        """2020 Tabulation State (FIPS)"""
        if x is None or x == "None":
            return False
        return (between('01',x,'02',2)) or (leftpad(x,2)==leftpad('72',2)) or (between('04',x,'06',2)) or (between('08',x,'13',2)) or (between('44',x,'51',2)) or (between('15',x,'42',2)) or (between('53',x,'56',2))
    @classmethod
    def is_valid_TABBLKCOU(self,x):
        """2020 Tabulation County (FIPS)"""
        if x is None or x == "None":
            return False
        return (between('001',x,'840',3))
    @classmethod
    def is_valid_TABTRACTCE(self,x):
        """2020 Tabulation Census Tract"""
        if x is None or x == "None":
            return False
        return (between('000100',x,'998999',6))
    @classmethod
    def is_valid_TABBLKGRPCE(self,x):
        """2020 Census Block Group"""
        if x is None or x == "None":
            return False
        return (between('0',x,'9',1))
    @classmethod
    def is_valid_TABBLK(self,x):
        """2020 Block Number"""
        if x is None or x == "None":
            return False
        return (between('0001',x,'9999',4))
    @classmethod
    def is_valid_EPNUM(self,x):
        """Privacy Edited Person Number"""
        if x is None or x == "None":
            return False
        x = str(x).strip()
        try:
            x = int(x)
        except ValueError:
            return False
        return (0 <= x <= 999999999)
    @classmethod
    def is_valid_RTYPE(self,x):
        """Record Type"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('5',1)) or (leftpad(x,1)==leftpad('3',1))
    @classmethod
    def is_valid_GQTYPE_PL(self,x):
        """Group Quarters Type"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('1',1)) or (leftpad(x,1)==leftpad('4',1)) or (leftpad(x,1)==leftpad('3',1)) or (leftpad(x,1)==leftpad('5',1)) or (leftpad(x,1)==leftpad('2',1)) or (leftpad(x,1)==leftpad('7',1)) or (leftpad(x,1)==leftpad('0',1)) or (leftpad(x,1)==leftpad('6',1))
    @classmethod
    def is_valid_VOTING_AGE(self,x):
        """Voting Age"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('1',1)) or (leftpad(x,1)==leftpad('2',1))
    @classmethod
    def is_valid_CENHISP(self,x):
        """Hispanic Origin"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('1',1)) or (leftpad(x,1)==leftpad('2',1))
    @classmethod
    def is_valid_CENRACE(self,x):
        """Census Race"""
        if x is None or x == "None":
            return False
        return (leftpad(x,2)==leftpad('04',2)) or (leftpad(x,2)==leftpad('17',2)) or (leftpad(x,2)==leftpad('19',2)) or (leftpad(x,2)==leftpad('23',2)) or (leftpad(x,2)==leftpad('20',2)) or (leftpad(x,2)==leftpad('13',2)) or (leftpad(x,2)==leftpad('56',2)) or (leftpad(x,2)==leftpad('49',2)) or (leftpad(x,2)==leftpad('24',2)) or (leftpad(x,2)==leftpad('01',2)) or (leftpad(x,2)==leftpad('38',2)) or (leftpad(x,2)==leftpad('48',2)) or (leftpad(x,2)==leftpad('03',2)) or (leftpad(x,2)==leftpad('54',2)) or (leftpad(x,2)==leftpad('14',2)) or (leftpad(x,2)==leftpad('18',2)) or (leftpad(x,2)==leftpad('33',2)) or (leftpad(x,2)==leftpad('35',2)) or (leftpad(x,2)==leftpad('28',2)) or (leftpad(x,2)==leftpad('43',2)) or (leftpad(x,2)==leftpad('21',2)) or (leftpad(x,2)==leftpad('36',2)) or (leftpad(x,2)==leftpad('08',2)) or (leftpad(x,2)==leftpad('26',2)) or (leftpad(x,2)==leftpad('29',2)) or (leftpad(x,2)==leftpad('32',2)) or (leftpad(x,2)==leftpad('06',2)) or (leftpad(x,2)==leftpad('34',2)) or (leftpad(x,2)==leftpad('15',2)) or (leftpad(x,2)==leftpad('40',2)) or (leftpad(x,2)==leftpad('45',2)) or (leftpad(x,2)==leftpad('61',2)) or (leftpad(x,2)==leftpad('62',2)) or (leftpad(x,2)==leftpad('51',2)) or (leftpad(x,2)==leftpad('59',2)) or (leftpad(x,2)==leftpad('52',2)) or (leftpad(x,2)==leftpad('02',2)) or (leftpad(x,2)==leftpad('42',2)) or (leftpad(x,2)==leftpad('46',2)) or (leftpad(x,2)==leftpad('47',2)) or (leftpad(x,2)==leftpad('50',2)) or (leftpad(x,2)==leftpad('09',2)) or (leftpad(x,2)==leftpad('30',2)) or (leftpad(x,2)==leftpad('41',2)) or (leftpad(x,2)==leftpad('16',2)) or (leftpad(x,2)==leftpad('44',2)) or (leftpad(x,2)==leftpad('58',2)) or (leftpad(x,2)==leftpad('53',2)) or (leftpad(x,2)==leftpad('05',2)) or (leftpad(x,2)==leftpad('55',2)) or (leftpad(x,2)==leftpad('12',2)) or (leftpad(x,2)==leftpad('39',2)) or (leftpad(x,2)==leftpad('07',2)) or (leftpad(x,2)==leftpad('57',2)) or (leftpad(x,2)==leftpad('31',2)) or (leftpad(x,2)==leftpad('10',2)) or (leftpad(x,2)==leftpad('22',2)) or (leftpad(x,2)==leftpad('60',2)) or (leftpad(x,2)==leftpad('25',2)) or (leftpad(x,2)==leftpad('63',2)) or (leftpad(x,2)==leftpad('11',2)) or (leftpad(x,2)==leftpad('27',2)) or (leftpad(x,2)==leftpad('37',2))

    @classmethod
    def validate_pipe_delimited(self,x):
        fields = x.split('|')
        if len(fields)!=13: return False
        if self.is_valid_SCHEMA_TYPE_CODE(fields[1]) == False: return False
        if self.is_valid_SCHEMA_BUILD_ID(fields[2]) == False: return False
        if self.is_valid_TABBLKST(fields[3]) == False: return False
        if self.is_valid_TABBLKCOU(fields[4]) == False: return False
        if self.is_valid_TABTRACTCE(fields[5]) == False: return False
        if self.is_valid_TABBLKGRPCE(fields[6]) == False: return False
        if self.is_valid_TABBLK(fields[7]) == False: return False
        if self.is_valid_EPNUM(fields[8]) == False: return False
        if self.is_valid_RTYPE(fields[9]) == False: return False
        if self.is_valid_GQTYPE_PL(fields[10]) == False: return False
        if self.is_valid_VOTING_AGE(fields[11]) == False: return False
        if self.is_valid_CENHISP(fields[12]) == False: return False
        if self.is_valid_CENRACE(fields[13]) == False: return False
        return True

class MDF_Person:
    __slots__ = ['SCHEMA_TYPE_CODE', 'SCHEMA_BUILD_ID', 'TABBLKST', 'TABBLKCOU', 'TABTRACTCE', 'TABBLKGRPCE', 'TABBLK', 'EPNUM', 'RTYPE', 'GQTYPE_PL', 'VOTING_AGE', 'CENHISP', 'CENRACE']
    def __repr__(self):
        return 'MDF_Person<SCHEMA_TYPE_CODE:{},SCHEMA_BUILD_ID:{},TABBLKST:{},TABBLKCOU:{},TABTRACTCE:{},TABBLKGRPCE:{},TABBLK:{},EPNUM:{},RTYPE:{},GQTYPE_PL:{},VOTING_AGE:{},CENHISP:{},CENRACE:{}>'.format(self.SCHEMA_TYPE_CODE,self.SCHEMA_BUILD_ID,self.TABBLKST,self.TABBLKCOU,self.TABTRACTCE,self.TABBLKGRPCE,self.TABBLK,self.EPNUM,self.RTYPE,self.GQTYPE_PL,self.VOTING_AGE,self.CENHISP,self.CENRACE)
    def __init__(self,line=None):
        if line:
            if '|' in line:
                self.parse_pipe_delimited(line)
            else:
                self.parse_column_specified(line)
    @classmethod
    def name(self):
        return 'MDF_Person'

    def parse_pipe_delimited(self,line):
        fields = line.split('|')
        if len(fields)!=13:
            raise ValueError(f'expected 13 fields, found {len(fields)}')
        self.SCHEMA_TYPE_CODE = fields[0]  # Schema Type Code
        self.SCHEMA_BUILD_ID = fields[1]  # Schema Build ID
        self.TABBLKST        = fields[2]  # 2020 Tabulation State (FIPS)
        self.TABBLKCOU       = fields[3]  # 2020 Tabulation County (FIPS)
        self.TABTRACTCE      = fields[4]  # 2020 Tabulation Census Tract
        self.TABBLKGRPCE     = fields[5]  # 2020 Census Block Group
        self.TABBLK          = fields[6]  # 2020 Block Number
        self.EPNUM           = fields[7]  # Privacy Edited Person Number
        self.RTYPE           = fields[8]  # Record Type
        self.GQTYPE_PL       = fields[9]  # Group Quarters Type
        self.VOTING_AGE      = fields[10]  # Voting Age
        self.CENHISP         = fields[11]  # Hispanic Origin
        self.CENRACE         = fields[12]  # Census Race

    def parse_column_specified(self,line):
        self.SCHEMA_TYPE_CODE = None   # no column information for SCHEMA_TYPE_CODE
        self.SCHEMA_BUILD_ID = None   # no column information for SCHEMA_BUILD_ID
        self.TABBLKST        = None   # no column information for TABBLKST
        self.TABBLKCOU       = None   # no column information for TABBLKCOU
        self.TABTRACTCE      = None   # no column information for TABTRACTCE
        self.TABBLKGRPCE     = None   # no column information for TABBLKGRPCE
        self.TABBLK          = None   # no column information for TABBLK
        self.EPNUM           = None   # no column information for EPNUM
        self.RTYPE           = None   # no column information for RTYPE
        self.GQTYPE_PL       = None   # no column information for GQTYPE_PL
        self.VOTING_AGE      = None   # no column information for VOTING_AGE
        self.CENHISP         = None   # no column information for CENHISP
        self.CENRACE         = None   # no column information for CENRACE

    def validate(self):
        """Return True if the object data validates"""
        if not MDF_Person_validator.is_valid_SCHEMA_TYPE_CODE(self.SCHEMA_TYPE_CODE): return False
        if not MDF_Person_validator.is_valid_SCHEMA_BUILD_ID(self.SCHEMA_BUILD_ID): return False
        if not MDF_Person_validator.is_valid_TABBLKST(self.TABBLKST): return False
        if not MDF_Person_validator.is_valid_TABBLKCOU(self.TABBLKCOU): return False
        if not MDF_Person_validator.is_valid_TABTRACTCE(self.TABTRACTCE): return False
        if not MDF_Person_validator.is_valid_TABBLKGRPCE(self.TABBLKGRPCE): return False
        if not MDF_Person_validator.is_valid_TABBLK(self.TABBLK): return False
        if not MDF_Person_validator.is_valid_EPNUM(self.EPNUM): return False
        if not MDF_Person_validator.is_valid_RTYPE(self.RTYPE): return False
        if not MDF_Person_validator.is_valid_GQTYPE_PL(self.GQTYPE_PL): return False
        if not MDF_Person_validator.is_valid_VOTING_AGE(self.VOTING_AGE): return False
        if not MDF_Person_validator.is_valid_CENHISP(self.CENHISP): return False
        if not MDF_Person_validator.is_valid_CENRACE(self.CENRACE): return False
        return True

    def validate_reason(self):
        reason=[]
        if not MDF_Person_validator.is_valid_SCHEMA_TYPE_CODE(self.SCHEMA_TYPE_CODE): reason.append('SCHEMA_TYPE_CODE ('+str(self.SCHEMA_TYPE_CODE)+') out of range (MPD-MPD)')
        if not MDF_Person_validator.is_valid_SCHEMA_BUILD_ID(self.SCHEMA_BUILD_ID): reason.append('SCHEMA_BUILD_ID ('+str(self.SCHEMA_BUILD_ID)+') out of range ()')
        if not MDF_Person_validator.is_valid_TABBLKST(self.TABBLKST): reason.append('TABBLKST ('+str(self.TABBLKST)+') out of range (01-02, 72-72, 04-06, 08-13, 44-51, 15-42, 53-56)')
        if not MDF_Person_validator.is_valid_TABBLKCOU(self.TABBLKCOU): reason.append('TABBLKCOU ('+str(self.TABBLKCOU)+') out of range (001-840)')
        if not MDF_Person_validator.is_valid_TABTRACTCE(self.TABTRACTCE): reason.append('TABTRACTCE ('+str(self.TABTRACTCE)+') out of range (000100-998999)')
        if not MDF_Person_validator.is_valid_TABBLKGRPCE(self.TABBLKGRPCE): reason.append('TABBLKGRPCE ('+str(self.TABBLKGRPCE)+') out of range (0-9)')
        if not MDF_Person_validator.is_valid_TABBLK(self.TABBLK): reason.append('TABBLK ('+str(self.TABBLK)+') out of range (0001-9999)')
        if not MDF_Person_validator.is_valid_EPNUM(self.EPNUM): reason.append('EPNUM ('+str(self.EPNUM)+') out of range (0-999999999)')
        if not MDF_Person_validator.is_valid_RTYPE(self.RTYPE): reason.append('RTYPE ('+str(self.RTYPE)+') out of range (5-5, 3-3)')
        if not MDF_Person_validator.is_valid_GQTYPE_PL(self.GQTYPE_PL): reason.append('GQTYPE_PL ('+str(self.GQTYPE_PL)+') out of range (1-1, 4-4, 3-3, 5-5, 2-2, 7-7, 0-0, 6-6)')
        if not MDF_Person_validator.is_valid_VOTING_AGE(self.VOTING_AGE): reason.append('VOTING_AGE ('+str(self.VOTING_AGE)+') out of range (1-1, 2-2)')
        if not MDF_Person_validator.is_valid_CENHISP(self.CENHISP): reason.append('CENHISP ('+str(self.CENHISP)+') out of range (1-1, 2-2)')
        if not MDF_Person_validator.is_valid_CENRACE(self.CENRACE): reason.append('CENRACE ('+str(self.CENRACE)+') out of range (04-04, 17-17, 19-19, 23-23, 20-20, 13-13, 56-56, 49-49, 24-24, 01-01, 38-38, 48-48, 03-03, 54-54, 14-14, 18-18, 33-33, 35-35, 28-28, 43-43, 21-21, 36-36, 08-08, 26-26, 29-29, 32-32, 06-06, 34-34, 15-15, 40-40, 45-45, 61-61, 62-62, 51-51, 59-59, 52-52, 02-02, 42-42, 46-46, 47-47, 50-50, 09-09, 30-30, 41-41, 16-16, 44-44, 58-58, 53-53, 05-05, 55-55, 12-12, 39-39, 07-07, 57-57, 31-31, 10-10, 22-22, 60-60, 25-25, 63-63, 11-11, 27-27, 37-37)')
        return ', '.join(reason)

    def SparkSQLRow(self):
        """Return a SparkSQL Row object for this object."""
        from pyspark.sql import Row
        return Row(
            schema_type_code=safe_str(self.SCHEMA_TYPE_CODE),
            schema_build_id=safe_str(self.SCHEMA_BUILD_ID),
            tabblkst=safe_str(self.TABBLKST),
            tabblkcou=safe_str(self.TABBLKCOU),
            tabtractce=safe_str(self.TABTRACTCE),
            tabblkgrpce=safe_str(self.TABBLKGRPCE),
            tabblk=safe_str(self.TABBLK),
            epnum=safe_int(self.EPNUM),
            rtype=safe_str(self.RTYPE),
            gqtype_pl=safe_str(self.GQTYPE_PL),
            voting_age=safe_str(self.VOTING_AGE),
            cenhisp=safe_str(self.CENHISP),
            cenrace=safe_str(self.CENRACE),
        )


    @staticmethod
    def parse_line(line):
        # Read a line and return it as a dictionary.
        inst: MDF_Person = MDF_Person()
        inst.parse_column_specified(line)
        assert inst.validate(), f'A line is invalid!! line: {line}, validate_reason: {inst.validate_reason()}'
        row = inst.SparkSQLRow()
        return row

    @staticmethod
    def parse_piped_line(line):
        # Read a pipe-delimited line and return it as a dictionary.
        inst: MDF_Person = MDF_Person()
        inst.parse_pipe_delimited(line)
        assert inst.validate(), f'A line is invalid!! line: {line}, validate_reason: {inst.validate_reason()}'
        row = inst.SparkSQLRow()
        return row



# Automatically generated on Thu Sep 24 09:39:22 2020 by C:\cygwin64\home\will0555\micah\etl_2020\ctools\schema\table.py

def leftpad(x,width):
    return '0'*(width-len(str(x)))+str(x)

def between(a,b,c,width):
    if len(b) > width:
        return False
    if '.' in a or '.' in b or '.' in c:
        try:
            return float(a) <= float(b) <= float(c)
        except ValueError:
            pass  # tries to return a float but might have weird input like 1.1.0 which will be compared traditionally instead
    b = b.replace(' ', '0')
    return leftpad(a,width) <= leftpad(b,width) <= leftpad(c,width)


def safe_int(i):
    try:
        return int(i)
    except (TypeError, ValueError) as e:
        return None

def safe_float(i):
    try:
        return float(i)
    except (TypeError, ValueError) as e:
        return None

def safe_str(i):
    try:
        return str(i)
    except (TypeError, ValueError) as e:
        return None


class MDF_Unit_validator:
    @classmethod
    def is_valid_SCHEMA_TYPE_CODE(self,x):
        """Schema Type Code"""
        if x is None or x == "None":
            return False
        return (leftpad(x,3)==leftpad('MUD',3))
    @classmethod
    def is_valid_SCHEMA_BUILD_ID(self,x):
        """Schema Build ID"""
        if x is None or x == "None":
            return False
        return True
    @classmethod
    def is_valid_TABBLKST(self,x):
        """2020 Tabulation State (FIPS)"""
        if x is None or x == "None":
            return False
        return (between('01',x,'02',2)) or (leftpad(x,2)==leftpad('72',2)) or (between('04',x,'06',2)) or (between('08',x,'13',2)) or (between('44',x,'51',2)) or (between('15',x,'42',2)) or (between('53',x,'56',2))
    @classmethod
    def is_valid_TABBLKCOU(self,x):
        """2020 Tabulation County (FIPS)"""
        if x is None or x == "None":
            return False
        return (between('001',x,'840',3))
    @classmethod
    def is_valid_TABTRACTCE(self,x):
        """2020 Tabulation Census Tract"""
        if x is None or x == "None":
            return False
        return (between('000100',x,'998999',6))
    @classmethod
    def is_valid_TABBLKGRPCE(self,x):
        """2020 Census Block Group"""
        if x is None or x == "None":
            return False
        return (between('0',x,'9',1))
    @classmethod
    def is_valid_TABBLK(self,x):
        """2020 Block Number"""
        if x is None or x == "None":
            return False
        return (between('0001',x,'9999',4))
    @classmethod
    def is_valid_RTYPE(self,x):
        """Record Type"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('2',1)) or (leftpad(x,1)==leftpad('4',1))
    @classmethod
    def is_valid_HH_STATUS(self,x):
        """Occupancy Status"""
        if x is None or x == "None":
            return False
        return (leftpad(x,1)==leftpad('0',1)) or (leftpad(x,1)==leftpad('1',1)) or (leftpad(x,1)==leftpad('2',1))

    @classmethod
    def validate_pipe_delimited(self,x):
        fields = x.split('|')
        if len(fields)!=9: return False
        if self.is_valid_SCHEMA_TYPE_CODE(fields[1]) == False: return False
        if self.is_valid_SCHEMA_BUILD_ID(fields[2]) == False: return False
        if self.is_valid_TABBLKST(fields[3]) == False: return False
        if self.is_valid_TABBLKCOU(fields[4]) == False: return False
        if self.is_valid_TABTRACTCE(fields[5]) == False: return False
        if self.is_valid_TABBLKGRPCE(fields[6]) == False: return False
        if self.is_valid_TABBLK(fields[7]) == False: return False
        if self.is_valid_RTYPE(fields[8]) == False: return False
        if self.is_valid_HH_STATUS(fields[9]) == False: return False
        return True

class MDF_Unit:
    __slots__ = ['SCHEMA_TYPE_CODE', 'SCHEMA_BUILD_ID', 'TABBLKST', 'TABBLKCOU', 'TABTRACTCE', 'TABBLKGRPCE', 'TABBLK', 'RTYPE', 'HH_STATUS']
    def __repr__(self):
        return 'MDF_Unit<SCHEMA_TYPE_CODE:{},SCHEMA_BUILD_ID:{},TABBLKST:{},TABBLKCOU:{},TABTRACTCE:{},TABBLKGRPCE:{},TABBLK:{},RTYPE:{},HH_STATUS:{}>'.format(self.SCHEMA_TYPE_CODE,self.SCHEMA_BUILD_ID,self.TABBLKST,self.TABBLKCOU,self.TABTRACTCE,self.TABBLKGRPCE,self.TABBLK,self.RTYPE,self.HH_STATUS)
    def __init__(self,line=None):
        if line:
            if '|' in line:
                self.parse_pipe_delimited(line)
            else:
                self.parse_column_specified(line)
    @classmethod
    def name(self):
        return 'MDF_Unit'

    def parse_pipe_delimited(self,line):
        fields = line.split('|')
        if len(fields)!=9:
            raise ValueError(f'expected 9 fields, found {len(fields)}')
        self.SCHEMA_TYPE_CODE = fields[0]  # Schema Type Code
        self.SCHEMA_BUILD_ID = fields[1]  # Schema Build ID
        self.TABBLKST        = fields[2]  # 2020 Tabulation State (FIPS)
        self.TABBLKCOU       = fields[3]  # 2020 Tabulation County (FIPS)
        self.TABTRACTCE      = fields[4]  # 2020 Tabulation Census Tract
        self.TABBLKGRPCE     = fields[5]  # 2020 Census Block Group
        self.TABBLK          = fields[6]  # 2020 Block Number
        self.RTYPE           = fields[7]  # Record Type
        self.HH_STATUS       = fields[8]  # Occupancy Status

    def parse_column_specified(self,line):
        self.SCHEMA_TYPE_CODE = None   # no column information for SCHEMA_TYPE_CODE
        self.SCHEMA_BUILD_ID = None   # no column information for SCHEMA_BUILD_ID
        self.TABBLKST        = None   # no column information for TABBLKST
        self.TABBLKCOU       = None   # no column information for TABBLKCOU
        self.TABTRACTCE      = None   # no column information for TABTRACTCE
        self.TABBLKGRPCE     = None   # no column information for TABBLKGRPCE
        self.TABBLK          = None   # no column information for TABBLK
        self.RTYPE           = None   # no column information for RTYPE
        self.HH_STATUS       = None   # no column information for HH_STATUS

    def validate(self):
        """Return True if the object data validates"""
        if not MDF_Unit_validator.is_valid_SCHEMA_TYPE_CODE(self.SCHEMA_TYPE_CODE): return False
        if not MDF_Unit_validator.is_valid_SCHEMA_BUILD_ID(self.SCHEMA_BUILD_ID): return False
        if not MDF_Unit_validator.is_valid_TABBLKST(self.TABBLKST): return False
        if not MDF_Unit_validator.is_valid_TABBLKCOU(self.TABBLKCOU): return False
        if not MDF_Unit_validator.is_valid_TABTRACTCE(self.TABTRACTCE): return False
        if not MDF_Unit_validator.is_valid_TABBLKGRPCE(self.TABBLKGRPCE): return False
        if not MDF_Unit_validator.is_valid_TABBLK(self.TABBLK): return False
        if not MDF_Unit_validator.is_valid_RTYPE(self.RTYPE): return False
        if not MDF_Unit_validator.is_valid_HH_STATUS(self.HH_STATUS): return False
        return True

    def validate_reason(self):
        reason=[]
        if not MDF_Unit_validator.is_valid_SCHEMA_TYPE_CODE(self.SCHEMA_TYPE_CODE): reason.append('SCHEMA_TYPE_CODE ('+str(self.SCHEMA_TYPE_CODE)+') out of range (MUD-MUD)')
        if not MDF_Unit_validator.is_valid_SCHEMA_BUILD_ID(self.SCHEMA_BUILD_ID): reason.append('SCHEMA_BUILD_ID ('+str(self.SCHEMA_BUILD_ID)+') out of range ()')
        if not MDF_Unit_validator.is_valid_TABBLKST(self.TABBLKST): reason.append('TABBLKST ('+str(self.TABBLKST)+') out of range (01-02, 72-72, 04-06, 08-13, 44-51, 15-42, 53-56)')
        if not MDF_Unit_validator.is_valid_TABBLKCOU(self.TABBLKCOU): reason.append('TABBLKCOU ('+str(self.TABBLKCOU)+') out of range (001-840)')
        if not MDF_Unit_validator.is_valid_TABTRACTCE(self.TABTRACTCE): reason.append('TABTRACTCE ('+str(self.TABTRACTCE)+') out of range (000100-998999)')
        if not MDF_Unit_validator.is_valid_TABBLKGRPCE(self.TABBLKGRPCE): reason.append('TABBLKGRPCE ('+str(self.TABBLKGRPCE)+') out of range (0-9)')
        if not MDF_Unit_validator.is_valid_TABBLK(self.TABBLK): reason.append('TABBLK ('+str(self.TABBLK)+') out of range (0001-9999)')
        if not MDF_Unit_validator.is_valid_RTYPE(self.RTYPE): reason.append('RTYPE ('+str(self.RTYPE)+') out of range (2-2, 4-4)')
        if not MDF_Unit_validator.is_valid_HH_STATUS(self.HH_STATUS): reason.append('HH_STATUS ('+str(self.HH_STATUS)+') out of range (0-0, 1-1, 2-2)')
        return ', '.join(reason)

    def SparkSQLRow(self):
        """Return a SparkSQL Row object for this object."""
        from pyspark.sql import Row
        return Row(
            schema_type_code=safe_str(self.SCHEMA_TYPE_CODE),
            schema_build_id=safe_str(self.SCHEMA_BUILD_ID),
            tabblkst=safe_str(self.TABBLKST),
            tabblkcou=safe_str(self.TABBLKCOU),
            tabtractce=safe_str(self.TABTRACTCE),
            tabblkgrpce=safe_str(self.TABBLKGRPCE),
            tabblk=safe_str(self.TABBLK),
            rtype=safe_str(self.RTYPE),
            hh_status=safe_str(self.HH_STATUS),
        )


    @staticmethod
    def parse_line(line):
        # Read a line and return it as a dictionary.
        inst: MDF_Unit = MDF_Unit()
        inst.parse_column_specified(line)
        assert inst.validate(), f'A line is invalid!! line: {line}, validate_reason: {inst.validate_reason()}'
        row = inst.SparkSQLRow()
        return row

    @staticmethod
    def parse_piped_line(line):
        # Read a pipe-delimited line and return it as a dictionary.
        inst: MDF_Unit = MDF_Unit()
        inst.parse_pipe_delimited(line)
        assert inst.validate(), f'A line is invalid!! line: {line}, validate_reason: {inst.validate_reason()}'
        row = inst.SparkSQLRow()
        return row



SPEC_CLASS_OBJECTS = [MDF_Person(),MDF_Unit()]
null = None
SPEC_DICT = {"tables": {"MDF_Person": {"name": "MDF_Person", "variables": [{"name": "SCHEMA_TYPE_CODE", "vtype": "CHAR", "position": "1", "desc": "Schema Type Code", "column": null, "width": 3, "ranges": [{"a": "MPD", "b": "MPD"}]}, {"name": "SCHEMA_BUILD_ID", "vtype": "CHAR", "position": "2", "desc": "Schema Build ID", "column": null, "width": 5, "ranges": []}, {"name": "TABBLKST", "vtype": "CHAR", "position": "3", "desc": "2020 Tabulation State (FIPS)", "column": null, "width": 2, "ranges": [{"a": "01", "b": "02"}, {"a": "72", "b": "72"}, {"a": "04", "b": "06"}, {"a": "08", "b": "13"}, {"a": "44", "b": "51"}, {"a": "15", "b": "42"}, {"a": "53", "b": "56"}]}, {"name": "TABBLKCOU", "vtype": "CHAR", "position": "4", "desc": "2020 Tabulation County (FIPS)", "column": null, "width": 3, "ranges": [{"a": "001", "b": "840"}]}, {"name": "TABTRACTCE", "vtype": "CHAR", "position": "5", "desc": "2020 Tabulation Census Tract", "column": null, "width": 6, "ranges": [{"a": "000100", "b": "998999"}]}, {"name": "TABBLKGRPCE", "vtype": "CHAR", "position": "6", "desc": "2020 Census Block Group", "column": null, "width": 1, "ranges": [{"a": "0", "b": "9"}]}, {"name": "TABBLK", "vtype": "CHAR", "position": "7", "desc": "2020 Block Number", "column": null, "width": 4, "ranges": [{"a": "0001", "b": "9999"}]}, {"name": "EPNUM", "vtype": "INT", "position": "8", "desc": "Privacy Edited Person Number", "column": null, "width": 9, "ranges": [{"a": "0", "b": "999999999"}]}, {"name": "RTYPE", "vtype": "CHAR", "position": "9", "desc": "Record Type", "column": null, "width": 1, "ranges": [{"a": "5", "b": "5"}, {"a": "3", "b": "3"}]}, {"name": "GQTYPE_PL", "vtype": "CHAR", "position": "10", "desc": "Group Quarters Type", "column": null, "width": 1, "ranges": [{"a": "1", "b": "1"}, {"a": "4", "b": "4"}, {"a": "3", "b": "3"}, {"a": "5", "b": "5"}, {"a": "2", "b": "2"}, {"a": "7", "b": "7"}, {"a": "0", "b": "0"}, {"a": "6", "b": "6"}]}, {"name": "VOTING_AGE", "vtype": "CHAR", "position": "11", "desc": "Voting Age", "column": null, "width": 1, "ranges": [{"a": "1", "b": "1"}, {"a": "2", "b": "2"}]}, {"name": "CENHISP", "vtype": "CHAR", "position": "12", "desc": "Hispanic Origin", "column": null, "width": 1, "ranges": [{"a": "1", "b": "1"}, {"a": "2", "b": "2"}]}, {"name": "CENRACE", "vtype": "CHAR", "position": "13", "desc": "Census Race", "column": null, "width": 2, "ranges": [{"a": "04", "b": "04"}, {"a": "17", "b": "17"}, {"a": "19", "b": "19"}, {"a": "23", "b": "23"}, {"a": "20", "b": "20"}, {"a": "13", "b": "13"}, {"a": "56", "b": "56"}, {"a": "49", "b": "49"}, {"a": "24", "b": "24"}, {"a": "01", "b": "01"}, {"a": "38", "b": "38"}, {"a": "48", "b": "48"}, {"a": "03", "b": "03"}, {"a": "54", "b": "54"}, {"a": "14", "b": "14"}, {"a": "18", "b": "18"}, {"a": "33", "b": "33"}, {"a": "35", "b": "35"}, {"a": "28", "b": "28"}, {"a": "43", "b": "43"}, {"a": "21", "b": "21"}, {"a": "36", "b": "36"}, {"a": "08", "b": "08"}, {"a": "26", "b": "26"}, {"a": "29", "b": "29"}, {"a": "32", "b": "32"}, {"a": "06", "b": "06"}, {"a": "34", "b": "34"}, {"a": "15", "b": "15"}, {"a": "40", "b": "40"}, {"a": "45", "b": "45"}, {"a": "61", "b": "61"}, {"a": "62", "b": "62"}, {"a": "51", "b": "51"}, {"a": "59", "b": "59"}, {"a": "52", "b": "52"}, {"a": "02", "b": "02"}, {"a": "42", "b": "42"}, {"a": "46", "b": "46"}, {"a": "47", "b": "47"}, {"a": "50", "b": "50"}, {"a": "09", "b": "09"}, {"a": "30", "b": "30"}, {"a": "41", "b": "41"}, {"a": "16", "b": "16"}, {"a": "44", "b": "44"}, {"a": "58", "b": "58"}, {"a": "53", "b": "53"}, {"a": "05", "b": "05"}, {"a": "55", "b": "55"}, {"a": "12", "b": "12"}, {"a": "39", "b": "39"}, {"a": "07", "b": "07"}, {"a": "57", "b": "57"}, {"a": "31", "b": "31"}, {"a": "10", "b": "10"}, {"a": "22", "b": "22"}, {"a": "60", "b": "60"}, {"a": "25", "b": "25"}, {"a": "63", "b": "63"}, {"a": "11", "b": "11"}, {"a": "27", "b": "27"}, {"a": "37", "b": "37"}]}]}, "MDF_Unit": {"name": "MDF_Unit", "variables": [{"name": "SCHEMA_TYPE_CODE", "vtype": "CHAR", "position": "1", "desc": "Schema Type Code", "column": null, "width": 3, "ranges": [{"a": "MUD", "b": "MUD"}]}, {"name": "SCHEMA_BUILD_ID", "vtype": "CHAR", "position": "2", "desc": "Schema Build ID", "column": null, "width": 5, "ranges": []}, {"name": "TABBLKST", "vtype": "CHAR", "position": "3", "desc": "2020 Tabulation State (FIPS)", "column": null, "width": 2, "ranges": [{"a": "01", "b": "02"}, {"a": "72", "b": "72"}, {"a": "04", "b": "06"}, {"a": "08", "b": "13"}, {"a": "44", "b": "51"}, {"a": "15", "b": "42"}, {"a": "53", "b": "56"}]}, {"name": "TABBLKCOU", "vtype": "CHAR", "position": "4", "desc": "2020 Tabulation County (FIPS)", "column": null, "width": 3, "ranges": [{"a": "001", "b": "840"}]}, {"name": "TABTRACTCE", "vtype": "CHAR", "position": "5", "desc": "2020 Tabulation Census Tract", "column": null, "width": 6, "ranges": [{"a": "000100", "b": "998999"}]}, {"name": "TABBLKGRPCE", "vtype": "CHAR", "position": "6", "desc": "2020 Census Block Group", "column": null, "width": 1, "ranges": [{"a": "0", "b": "9"}]}, {"name": "TABBLK", "vtype": "CHAR", "position": "7", "desc": "2020 Block Number", "column": null, "width": 4, "ranges": [{"a": "0001", "b": "9999"}]}, {"name": "RTYPE", "vtype": "CHAR", "position": "8", "desc": "Record Type", "column": null, "width": 1, "ranges": [{"a": "2", "b": "2"}, {"a": "4", "b": "4"}]}, {"name": "HH_STATUS", "vtype": "CHAR", "position": "9", "desc": "Occupancy Status", "column": null, "width": 1, "ranges": [{"a": "0", "b": "0"}, {"a": "1", "b": "1"}, {"a": "2", "b": "2"}]}]}}}
