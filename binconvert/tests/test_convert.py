from .. import convert, utils
import os
import struct
import sys
import unittest


class TestConvert(unittest.TestCase):
    def gen_binary_file(self, source, *content, **kwargs):
        """
        Generate the sample binary file for the test
        """
        byte_order = kwargs.get('byte_order', sys.byteorder)
        fmt = kwargs.get('fmt', self.fmt)

        # This tells the struct library the byte order when packing/unpacking
        if byte_order == 'little':
            fmt = '<{0}'.format(fmt)
        else:
            fmt = '>{0}'.format(fmt)
        with open(source, 'wb') as f:
            f.write(struct.pack(fmt, *content))

    def read_binary_file(self, source, **kwargs):
        """
        Read the binary files made by the test
        """
        byte_order = kwargs.get('byte_order', sys.byteorder)
        fmt = kwargs.get('fmt', self.fmt)

        # This tells the struct library the byte order when packing/unpacking
        if byte_order == 'little':
            fmt = '<{0}'.format(fmt)
        else:
            fmt = '>{0}'.format(fmt)
        with open(source, 'rb') as f:
            stream = f.read()
            return struct.unpack(fmt, stream)

    def setUp(self):
        self.fmt = '3s3si3si'
        self.formats = ['3s', '3si:#']
        self.lsource = 'l.bin'
        self.bsource = 'b.bin'
        self.content = ('foo', 'bar', 26, 'baz', 32)
        self.gen_binary_file(self.lsource, *self.content,
                             byte_order='little')
        self.gen_binary_file(self.bsource, *self.content, byte_order='big')

    def tearDown(self):
        os.remove(self.lsource)
        os.remove(self.bsource)
        try:
            os.remove('test.bin')
        except OSError:
            return

    def test_convert_default(self):
        """
        Test default behavior of convert which is a simple byte swap to native
        byte-ordering.
        """
        if sys.byteorder == 'little':
            test_byte_order = 'big'
        else:
            test_byte_order = 'little'

        self.gen_binary_file('test.bin', '\xab\xcd',
                             byte_order=test_byte_order, fmt='2s')
        convert('test.bin')
        result, = self.read_binary_file('test.bin', fmt='2s')
        self.assertEqual('\xcd\xab', result)

    def test_convert_big_to_little(self):
        """
        Convert from big to little endian
        """
        convert(self.bsource, 'test.bin', byte_order='little', fmt=self.fmt)
        result = self.read_binary_file('test.bin', byte_order='little',
                                       fmt=self.fmt)
        self.assertEqual(self.content, result)

    def test_convert_little_to_big(self):
        """
        Convert from little to big endian
        """
        convert(self.lsource, 'test.bin', byte_order='big', fmt=self.fmt)
        result = self.read_binary_file('test.bin', byte_order='big',
                                       fmt=self.fmt)
        self.assertEqual(self.content, result)

    def test_gen_format_string_pound(self):
        """
        Calculate format string with pound
        """
        fmt, _ = utils.gen_format_string(self.formats,
                                         size=os.path.getsize(self.bsource))
        self.assertEqual('3s3si3si', fmt)

    def test_gen_format_string_counts(self):
        """
        Calculate format string with counts given
        """
        fmt, _ = utils.gen_format_string(['i', '2sf:3', 'h'])
        self.assertEqual('i2sf2sf2sfh', fmt)
