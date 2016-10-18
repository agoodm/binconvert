import os
import struct
import sys


def convert(source, destination=None, byte_order=None, fmt=None):
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
    destination : str, optional
        The path to the converted output file. If not specified, source is
        overwritten.
    byte_order : {None, 'little', 'big'}
        The byte order to convert to (endianness). If not specified, the
        native byte ordering of your platform is used (eg, 'little' on x86).
        "Do nothing" conversion operations are not allowed, so the input file
        given by source will be assumed to be formatted in the opposite
        byte order.
    fmt : str, optional
        Format string. See documentation for the python struct module for
        valid examples. The string should span the entire size of the file you
        are converting. The default format is "Nh", where N is half the size of
        the file in bytes, swapping each even and odd byte. For this case, the
        total size of the file in bytes must be even.
    """
    # This format string gives the number of bytes and type
    # for each piece of data in the record.
    if fmt is None:
        num = os.path.getsize(source)
        fmt = '{0}h'.format(num/2)

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
