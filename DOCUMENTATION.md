# Netzob Model documentation

This document describes the components of the model used internally by Netzob. It is essentially a shortened and extended version of the [Netzob Language Specification](https://gdr-securite.irisa.fr/wp-content/uploads/sujet17-amossys.pdf).

## Overview

The top-level object of Netzob's language specification is a **Symbol**, which could also be called a *message format*; it describes the syntax (and some semantics) of a particular type of message.
A Symbol is made up of one or more **Fields**, which encapsulate **Variables** in the form of a tree.
There are two fundamental kinds of Variables: *Leaf Variables*, which accept no children (these are **Data Variables**, which encapsulate primitive types, and **Relationship Variables**, which define that the content of this variable depends on the size or value of another variable), and *Node Variables*, which do accept children. The latter can be either an **Aggregate** (a concatenation of variables), an **Alternate** (a choice of one of its children), or a **Repetition** of its child node.

## Data variables

Data variables encapsulate primitive types. They store the data type (which is a primitive type), they current value of the data (which can be none), and a State Variable Assignment Strategy (SVAS).

A SVAS can be one of these cases:
* `CONSTANT`: Constant data, e.g. identifiers that stay constant in the entire protocol.
* `PERSISTENT`: Data that stays constant for a session, e.g. session identifiers or some network addresses. Essentially, they store a "write-once" value that does not have to be initially defined (unlike constants, which must always be defined).
* `EPHEMERAL`: Data that changes whenever it is generated; however, its value is stored and can be used e.g. by other fields.
* `VOLATILE`: Data that changes whenever it is generated and is never stored.

## Primitive types

The following primitive types are supported:

* Integer (a number)
* HexaString (sequence of bytes of arbitrary size)
* BLOB/Raw (sequence of bytes of arbitrary size)
* BitArray (sequence of bits of arbitrary size)
* IPv4 (IP address)
* ASCII (string data)
* Timestamp (date)

## [All Types]

All types derive from a common AbstractType class.
It uses the following information relevant to IPM creation:

* `value`: The current value
* `size`: The total size of this type in bits; for most types (but not integers), this is a tuple that defines the (minimum, maximum) size in bits.
* `unitSize`: The size of a single value in bits (1, 4, 8, 16, 32 or 64 bits; default: 8)
* `endianness`: Big or Little Endian encoding (default: big endian) *(can possibly be ignored for IPMs)*
* `sign`: Signed or unsigned (default: unsigned) *(can possibly be ignored for IPMs)*

### Integer

A numeric value. This type additionally has the following parameters:

* `interval`: A minimum and maximum value *(this is NOT stored anywhere right now, but only used to compute the size!)*

The `size` parameter is computed automatically (based on `size`, `interval`, or `value`) and passed to AbstractType.

Proposal: Store `interval` during initialization so we can use it to generate boundary values

#### Examples

```
Integer(20)
Integer(interval=(-130, 10), sign=AbstractType.SIGN_SIGNED)
```

### HexaString

A hexadecimal string that is used to define binary data of arbitrary length.
This type has no additional parameters.

The `value` is converted to a bitarray.

#### Examples

```
HexaString("DEADBEEF")
HexaString("F00D", size=(8, 64))
```

### Raw

Raw binary data expressed in bytes. This type additionally has the following parameters:

* `nbBytes`: Either a single integer defining the size in bytes, or a tuple of (min, max) byte size.
* `alphabet`: A list of allowed values for this type.

#### Examples

```
Raw(b'\x00\x06')
Raw(nbBytes=(2, 16), alphabet=['a', 'b', 'c'])
```

### BitArray

Raw binary data expressed in bits. This type has no additional parameters.

#### Examples

```
BitArray(bitarray([0,1,0,1,1]))
BitArray(nbBits=3)
BitArray(nbBits=(4,12))
```

### IPv4

An IP address. This type additionally has the following parameters:

* `network`: An allowed network in CIDR notation that can be parsed as an `IPNetwork` by the Python `netaddr` library. If not given (and `value` is empty), the internal `generate()` function picks a random non-private network.

The `generate()` function for this type is slightly buggy if neither `network` nor `value` are set. It over-restricts the range of allowed IPs by filtering out all ranges that are in the same `/8` as any private network. Simultaneously, it has a small chance of accidentally generating broadcast addresses.

#### Examples

```
IPv4("192.168.88.123")
IPv4(network="111.222.0.0/16")
IPv4()
```

### ASCII

A string type. Despite the name, this type can also store non-ASCII characters (if `value` is given as a bitarray), but its `generate()` function only ever generates ASCII strings.
This type additionally has the following parameters:

* `nbChars`: A minimum and maximum number of characters allowed for this string. Default is `(0, AbstractType.MAXIMUM_GENERATED_DATA_SIZE)`.

This type additionally defines a `mutate()` function that generates the uppercase, lowercase, reversed, and reversed lowercase/uppercase version of a value (or the output of the `generate()` function if no value is defined).
The regular `mutate()` function instead does some endianness reversal mutations.

#### Examples

```
ASCII("some constant string value")
ASCII(nbChars=(4,16))
```

### Timestamp

A timestamp value defined for a variety of formats. This type additionally has the following parameters:

* `epoch`: An epoch (i.e. definition for the value `0`); this supports e.g. Windows (`1601-01-01`), UNIX (`1970-01-01`) and NTP (`1900-01-01`).
* `unity`: The type of unit contained in this timestamp; e.g. seconds, miliseconds, or nanoseconds.

The internal size of such a value is always 32 bits (although the `unitSize` parameter can be different).

The current `generate()` method simply returns the current time.


#### Examples

```
Timestamp(epoch=Timestamp.EPOCH_WINDOWS,unitSize=AbstractType.UNITSIZE_64)
Timestamp(123456789, unity=Timestamp.UNITY_MICROSECOND)
```

## Relationship Variables

The following types of relationship variables are defined:

* InternetChecksum (a RFC 1071 checksum over one or more fields)
* Value (applies a Python function to compute the value of a field from another)
* Size (the total size of one or more fields)

All relationship variables have a type and an optional list of field dependencies (i.e. the fields this variable depends on).
The SVAS of a relationship variable is always `VOLATILE`.

The `Value` relationship takes an additional parameter that defines the Python callback used to compute the value; this callback must take the value of one field as its own parameter.

The `Size` relationship additionally takes the parameters `factor` (a factor multiplied with the number of bits to obtain the value of the size field, 1/8 by default) and `offset` (added to the aforementioned multiplication to obtain the final size value).

#### Examples

```
seqField = Field(name="Sequence Number", domain=Raw(b'\\x00\\x07'))
timeField = Field(name="Timestamp", domain=Raw(b'\\xa8\\xf3\\xf6\\x53\\x00\\x00\\x00\\x00'))
sizeField = Field(Size([seqField, timeField]), name="Size")
chksumField = Field(name="Checksum")
chksumField.domain = InternetChecksum([seqField, timeField, sizeField], dataType=Raw(nbBytes=2))
s = Symbol(fields=[seqField,timeField,sizeField,chksumField])
s.messages = [RawMessage(s.specialize())]
print(s)
```

## Node Variables

Node variables can have one or more children and optionally a SVAS.

The following node variables exist (they are handled in the same priority as this list, first entry is the most "fundamental" one):

* `Repeat`: Repeats one child node. This type additionally takes two parameters: An optional `delimiter` that will be seen between multiple values of the child, and a `nbRepeat` parameter that defines the number of repetitions; this can be either a single integer, a tuple specifying the minimum and maximum number of repetitions, another field (that acts as a terminator), or a custom callback that returns a boolean indicating whether the correct number of repetitions has been reached.
* `Agg`: A concatenation of variables.
* `Alt`: An alternative between variables.

### Regex comparison

* The `Repeat` node behaves like the `{}` operator in regular expressions, e.g. `abc{1,3}` or `a{5}`.
* The `Alt` node behaves like the `|` operator, e.g. `(foo|bar|baz)`.
* The `Agg` node behaves like simply grouping one symbol after the other (other than that, the behavior is implicit to regular expressions)

#### Examples

```
Field(Repeat(ASCII("netzob"), nbRepeat=(0,3)))
Field(Agg([BitArray(bitarray('01101001')), BitArray(nbBits=3), BitArray(nbBits=5)]))
Field(Alt([ASCII("foo"), ASCII("bar")]))
```
