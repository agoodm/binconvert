# binconvert
A CLI utility for converting byte orders in binary files from one platform to another.

# Introduction and Motivation
`binconvert` is a program that was born out of the author's need to read old files that were written in a *binary* format on a SPARC system. Because SPARC's native byte-ordering is *big endian* (ie, most significant byte first), this caused comptatability issues when porting these files over to an x86 Linux machine (which has *little endian*, or least significant byte first native byte-ordering). In an ideal world where the binary files are *unstructured* and every data value stored in the file has the same type, one could easily get around this problem by either recompiling their program with special compiler flags or using some existing CLI solutions like `dd conv=swab`. 

Unfortunately there are many binary files which are *structured*, ie the variables stored in the file are of different lengths and types, and so it becomes necessary to know the internal structure of the file beforehand. Thankfully, python provides an easy to use [`struct`](https://docs.python.org/3/library/struct.html) module which allows for users to express the structure and byte-ordering of the data as a format string. For example, "f6s" would imply that the first 4 bytes in the file represent a floating point number, while the remaining 6 bytes designate a 6 character string. 

Although this is a much nicer alternative than forcing the user to manually perform the byte-swapping by hand, it can still break down when needing to process larger binary files with more complex structures. As an example, consider a binary file named `a.bin` which represents the following table:

| Name | Age(yr) | Weight(lb) | Height(ft) |
|------|---------|------------|------------|
| Alex | 26      | 170.5      | 6.0        |

Now imagine if this table had hundreds of additional entries. The format string required by `struct` can easily become very long. However, we know that it can be generalized as a *header* which labels each column in the table ("4s7s10s10s") followed by the actual entries of the table ("4si2f"), so it should be possible to generate the format string for an arbitrary number of entries. Using `binconvert`, without even knowing the total size of the file beforehand, we can easily convert its byte-ordering from big to little-endian on an x86 machine using:

```sh
bconv a.bin -f 4s7s10s10s 4si2f:*
```

In summary, `binconvert`'s main purpose is to extend the functionality of the python [`struct`](https://docs.python.org/3/library/struct.html) module for these use cases by doing the following:

1. Make it easier to generate format strings for larger files.
2. Provide a simple CLI interface for performing the endianness conversion.

# Installation
## Release Versions
To install the latest release version of `binconvert`, use `pip`:
```sh
pip install binconvert
```
In the near future, an installation method using `conda` will also be provided.
## From Source
To install from the latest codebase, use:
```sh
git clone https://github.com/agoodm/binconvert.git
cd binconvert
python setup.py install
```

# Usage
If all goes well, you should be able to execute the program with:
```sh
bconv
```

For further documentation, use the `-h` switch (`bconv -h`).
