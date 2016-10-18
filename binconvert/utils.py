import os
import struct
import yaml


def read_from_config_file(configfile):
    """
    Read the format patterns from the given YAML configuration file.

    Parameters
    ----------
    configfile : str
        Path to YAML config file to read from.

    Returns
    -------
    formats : list of str
        A list of strings of the form
        ["<pattern1>:<count1>", "<pattern2>:<count2>", ...]. Each instance of
        ":<countN>" can be omitted for format patterns that only occur once.
    """
    with open(configfile, 'r') as f:
        formats = yaml.load(f)['formats']

    return formats


def write_to_config_file(configfile, formats):
    """
    Read the format patterns from the given YAML configuration file.

    Parameters
    ----------
    configfile : str
        Path to YAML config file to read from.
    formats : list of str
        A list of strings of the form
        ["<pattern1>:<count1>", "<pattern2>:<count2>", ...]. Each instance of
        ":<countN>" can be omitted for format patterns that only occur once.
    """
    with open(configfile, 'w') as f:
        yaml.dump({'formats': formats}, f, default_flow_style=False)


def gen_format_string(formats, size=None, expand=False):
    """
    Generate a format string specifying the byte alignment given a list of the
    form ["<pattern1>:<count1>", "<pattern2>:<count2>", ...]. For example,

    >>> gen_format_string(["id4s:2", "f2d"])

    would return "id4sid4sf2d".

    For convenience, a special pound (*) character can be used once to
    automatically determine the count of one pattern. As an example,

    >>> gen_format_string(["i", "8s:*"])

    would return "i8s8s" if size is 20 bytes.

    Parameters
    ----------
    formats : list of str
        A list of strings of the form
        ["<pattern1>:<count1>", "<pattern2>:<count2>", ...], where each count is
        the number of repeated occurences of each format pattern. Each instance
        of ":<countN>" can be omitted for format patterns that only occur once.
        In the special case that a <countN> "*", the remainder
        of the available bytes in the file is used to automatically calculate
        the count. This can only be done once per list of formats.
    size : int, optional
        size of the source file in bytes. Only needed if wilcard '*' character
        is used in counts.
    expand : bool, optional
        If True, expand the pound in the output formats list. This should be
        left False (default) if you are working with many binary files with a
        common format patterns but of different size. This does nothing is size
        is None (ie no source file is given).

    Returns
    -------
    fmt : str
        The full format string.
    formats : list of str
        Formats list with pound count expanded to actual counts
        if expand is True.
    """
    fmt = ''
    # Use this to keep track of size expended by format so far.
    cumsize = 0
    special_pattern = None
    special_index = None
    for i, pattern_info in enumerate(formats):
        pattern_info = pattern_info.split(':')
        pattern = pattern_info[0]

        # count is 1 if not given.
        if len(pattern_info) == 1:
            cumsize += struct.calcsize('=' + pattern)
            fmt += pattern
        elif pattern_info[1][-1] == '*':
            if special_pattern:
                raise struct.error('Wildcard (*) character may only be used once')

            # We will need the current pattern and count values for later
            # when the remaining size is fully calculated.
            special_pattern = pattern
            special_index = i

            # Until remaining size is fully calculated, set a placeholder.
            fmt += '{0}'
        else:
            count = int(pattern_info[1])
            result = count*pattern
            cumsize += struct.calcsize('=' + result)
            fmt += result

    # We are now ready to allocate the remaining bytes
    # for the special '*' pattern.
    if special_pattern:
        # Make sure source is specified, otherwise return.
        if size is None:
            return fmt, formats

        # Calculate the count such that pattern evenly fits in remaining size
        remaining = size - cumsize
        chunksize = struct.calcsize('=' + special_pattern)
        count = remaining / chunksize
        if remaining % chunksize != 0:
            raise struct.error('Given chunksize of {0} bytes does not divide '
                               'evenly into remaining number of bytes.'
                               .format(chunksize))

        result = count*special_pattern
        fmt = fmt.format(result)

        # Update formats list to expand * character.
        if expand:
            formats[special_index] = formats[special_index].replace('*', str(count))

    # Final sanity check: Ensure format string size and source file size match.
    fmt_size = struct.calcsize('=' + fmt)
    if size and size != fmt_size:
        raise struct.error('Format string size and chunk size do not match.\n'
                           'Expected: {0}, Got: {1}'.format(size, fmt_size))

    return fmt, formats
