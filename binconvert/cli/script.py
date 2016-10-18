from __future__ import print_function

import argparse
import os
import struct
import sys
import yaml

import binconvert
from binconvert import convert
from binconvert.utils import (gen_format_string, write_to_config_file,
                              read_from_config_file)


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
                        ' For example, "bconv a.bin -f i 4s:*" will generate'
                        ' "i4s4s" as a format string when a.bin is 12 bytes.')
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
        print(binconvert.__version__)
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
            formats = ['h:*']

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
