from __future__ import print_function

import argparse
import os
import struct
import sys
import yaml

__version__ = '0.1.0'

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

    For convenience, a special wildcard (*) character can be used once to
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
        If True, expand the wildcard in the output formats list. This should be
        left False (default) if you are working with many binary files with a
        common format patterns but of different size. This does nothing is size
        is None (ie no source file is given).

    Returns
    -------
    fmt : str
        The full format string.
    formats : list of str
        Formats list with wildcard count expanded to actual counts
        if expand is True.
    """
    # Fallback format
    if formats == ['*']:
        return '*', formats

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
            cumsize += struct.calcsize(pattern)
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
            cumsize += struct.calcsize(result)
            fmt += result

    # We are now ready to allocate the remaining bytes
    # for the special '*' pattern.
    if special_pattern:
        # Make sure source is specified, otherwise return.
        if size is None:
            return fmt, formats

        # Calculate the count such that pattern evenly fits in remaining size
        remaining = size - cumsize
        chunksize = struct.calcsize(special_pattern)
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


def convert(source, destination=None, byte_order=None, fmt='*'):
    """
    Converts the given file (specified by source) from one byte order
    to another. For example, to convert a file in the current working directory
    from big to little endian, call

    >>> convert('a.bin', 'little')

    By default, the source file is overwritten. To prevent this, a destination
    path may optionally be specified. Additionally, not specifying order
    will assume that you are trying to convert to the native byte order of your
    platform. Eg,

    >>> convert('a.bin', 'b.bin')

    will convert a.bin from big endian to little endian and store the result
    in b.bin on x86 platforms.

    Parameters
    ----------
    source : str
        The path to the binary file to be converted.
    destination: str, optional
        The path to the converted output file. If not specified, source is
        overwritten.
    byte_order: {None, 'little', 'big'}
        The byte order to convert to (endianness). If not specified, the
        native byte ordering of your platform is used (eg, 'little' on x86).
        "Do nothing" conversion operations are not allowed, so the input file
        given by source will be assumed to be formatted in the opposite
        byte order.
    fmt: str, optional
        Format string. See documentation for the python struct module for
        valid examples. The string should span the entire size of the file you
        are converting. The default format is "Nc", where N is the size of the
        file in bytes. Thus the bytes of the entire file are reversed in one go.
    """
    # This format string gives the number of bytes and type
    # for each piece of data in the record.
    if fmt == '*':
        num = os.path.getsize(source)
        fmt = num*'c'

    # Set default destination path to source (overwrite)
    if destination is None:
        destination = source

    # Set default byte order to native
    if byte_order is None:
        byte_order = sys.byteorder

    # This tells the struct library the byte order when packing/unpacking
    if byte_order == 'little':
        fmt_in = '>{0}'.format(fmt)
        fmt_out = '<{0}'.format(fmt)
    else:
        fmt_in = '<{0}'.format(fmt)
        fmt_out = '>{0}'.format(fmt)

    # Read and convert the data from source file
    with open(source, 'rb') as f:
        stream = f.read()
        data = struct.unpack(fmt_in, stream)

    # Write converted data to destination file
    with open(destination, 'wb') as f:
        f.write(struct.pack(fmt_out, *data))


def main():
    """
    CLI script for convert function.
    """
    description = 'Convert files from one byte order to another.'
    parser = argparse.ArgumentParser(prog='bconv', description=description)
    parser.add_argument('source', nargs='?', help='Path to input file')
    parser.add_argument('destination', nargs='?', help='Path to output file')
    parser.add_argument('--byte-order', dest='order', help='Output file byte order')
    parser.add_argument('-l', '--little-endian', dest='little', action='store_true',
                        help='Use little endian byte ordering for destination.')
    parser.add_argument('-b', '--big-endian', dest='big', action='store_true',
                        help='Use big endian byte ordering for destination.')
    parser.add_argument('-f', '--format', nargs='*', help='Format string.'
                        ' See documentation for the python standard library'
                        ' struct module for valid examples. To shorten the format'
                        ' string with common patterns, you may use the following'
                        ' notation:\n'
                        ' <pattern1>:<count1> <pattern2>:<count2> ...\n Omitting'
                        ' the : assumes a count of 1. As an example, "-f d i2s:2" is'
                        ' equivalent to "-f di2si2s". In addition, one of the'
                        ' counts may have a special wildcard character (*).'
                        ' When source is given, the count is automatically'
                        ' converted such that the number of bytes represented by'
                        ' pattern*count fits into the remainder of available bytes.'
                        ' For example, "bconv a.bin -p -f i 4s:*" will print'
                        ' "i4s4s" when a.bin is 12 bytes.')
    parser.add_argument('-d', '--set-default-format', dest='store', action='store_true',
                        help='If true, the format specified with the -f or -c'
                        ' switch is stored in the ~/.bconvrc file.'
                        ' Any formats containing a "*" are expanded.')
    parser.add_argument('-c', '--configfile', help='If specified, override the '
                        'default ~/.bconvrc for loading the the format string. '
                        'This is useful in place of the -f switch for really '
                        'long format strings.')
    parser.add_argument('-p', '--print-format', dest='printf', action='store_true',
                        help='Print the currently used format string. Omitting'
                        ' all other arguments prints the format string stored in'
                        ' the ~/.bconv file that comes with this program.')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Print current version of this program and exit.')
    parser.add_argument('-e', '--expand', action='store_true',
                        help='If set, the special wildcard (*) count will not'
                        ' be replaced after the actual format pattern count is'
                        ' is calculated. This behavior is not the default because'
                        ' more often than not, uses cases involve multiple binary'
                        ' files with different sizes but common format patterns'
                        ' which make it more convenient to keep the "*" count intact'
                        ' if setting it as the default format with -d.')

    # Now process the arguments
    args = parser.parse_args()

    # Print help message if arguments are default.
    if not (args.source or args.destination or args.order or args.big
            or args.little or args.format or args.store or args.configfile
            or args.printf or args.version or args.expand):
        parser.print_usage()
        sys.exit()

    if args.version:
        print(__version__)
        sys.exit()

    # Input file
    source = args.source
    size = None

    # Ensure source is valid if given
    if source:
        try:
            size = os.path.getsize(source)
        except OSError as e:
            parser.error(e)

    # Output file
    destination = args.destination

    # Byte order
    if ((args.order is not None and (args.big or args.little))
        or (args.big and args.little)):
        parser.error('Cannot specify multiple byte-orders.')

    if args.big:
        byte_order = 'big'

    elif args.little:
        byte_order = 'little'

    else:
        byte_order = args.order

    # Format string
    configfile = os.path.join(os.path.expanduser('~'), '.bconvrc')
    if args.format and args.configfile:
        parser.error('Multiple format strings specified, please use only one of'
                     ' -f and -c when overriding default format.')
    elif args.format:
        formats = args.format

    elif args.configfile:
        try:
            configfile = args.configfile
            formats = read_from_config_file(args.configfile)

        except IOError as e:
            parser.error(e)

    else:
        try:
            formats = read_from_config_file(configfile)
        except IOError as e:
            # Do this in case default config file is corrupted or doesn't exist.
            formats = ['*']

    # Finally we can generate the full format string
    try:
        fmt, expanded_formats = gen_format_string(formats, size, args.expand)
    except struct.error as e:
        parser.error(e)

    # Store default format in config file
    if args.store or (args.format is None and expanded_formats != formats):
        write_to_config_file(configfile, expanded_formats)

    # Print the format string
    if args.printf:
        print(yaml.dump({'Current Formats': formats},
                        default_flow_style=False)[:-1])

    # If source isn't given, we're done.
    if not source:
        return

    # Do the actual byte order conversion.
    try:
        convert(source, destination, byte_order, fmt)
    except IOError as e:
        # source input file can't be read
        parser.error(e)
    except struct.error as e:
        # badly formed format string
        parser.error(e)


if __name__ == '__main__':
    main()
