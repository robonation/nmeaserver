import operator
import re
from functools import reduce

#: RegEx pattern for a strict NMEA sentence (mandatory checksum).
NMEApattern_strict = re.compile('''
        ^[^$]*\$?
        (?P<nmea_str>
            (?P<talker>\w{2})
            (?P<sentence_type>\w{3}),
            (?P<data>[^*]+)
        )(?:\\*(?P<checksum>[A-F0-9]{2}))
        [\\\r\\\n]*
        ''', re.X | re.IGNORECASE)

#: RegEx pattern for a lax NMEA sentence (optional checksum).
NMEApattern = re.compile('''
        ^[^$]*\$?
        (?P<nmea_str>
            (?P<talker>\w{2})
            (?P<sentence_type>\w{3}),
            (?P<data>[^*]+)
        )
        [\\\r\\\n]*
        ''', re.X | re.IGNORECASE)


def calc_checksum(nmea_str):
    # Strip '$' and everything after the '*'
    if nmea_str.startswith('$'):
        nmea_str = nmea_str[1:]
    if nmea_str.find('*') >= 0:
        nmea_str = nmea_str[:nmea_str.find('*')]

    # this returns a 2 digit hexadecimal string to use as a checksum.
    checksum = hex(reduce(operator.xor, map(ord, nmea_str), 0))[2:].upper()
    if len(checksum) == 2:
        return checksum
    else:
        return '0' + checksum


def format(sentence, new_line=False):
    if sentence.find('*') < 0:
        sentence = sentence + '*' + calc_checksum(sentence)
    if sentence.startswith('$') is False:
        sentence = '$' + sentence
    if new_line:
        sentence + '\r' + '\n'
    return sentence


def parse(nmea_str, strict=True):
    # parse NMEA string into dict of fields.
    # the data will be split by commas and accessible by index.
    match = None
    if strict:
        match = NMEApattern_strict.match(nmea_str)
    else:
        match = NMEApattern.match(nmea_str)

    if not match:
        raise ValueError('Could not parse data:', nmea_str)
    nmea_dict = {}
    nmea_dict['sentence'] = nmea_str
    nmea_str = match.group('nmea_str')
    nmea_dict['sentence_id'] = match.group('talker').upper() + \
        match.group('sentence_type').upper()
    nmea_dict['talker'] = match.group('talker').upper()
    nmea_dict['sentence_type'] = match.group('sentence_type').upper()
    nmea_dict['data'] = match.group('data').split(',')

    if strict:
        checksum = match.group('checksum')
        # check the checksum to ensure matching data.
        if checksum != calc_checksum(nmea_str):
            raise ValueError(
                'Checksum does not match: %s != %s.' %
                (checksum, calc_checksum(nmea_str)))
    return nmea_dict
