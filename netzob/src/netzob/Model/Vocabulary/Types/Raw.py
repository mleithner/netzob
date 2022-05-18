# -*- coding: utf-8 -*-

# +---------------------------------------------------------------------------+
# |          01001110 01100101 01110100 01111010 01101111 01100010            |
# |                                                                           |
# |               Netzob : Inferring communication protocols                  |
# +---------------------------------------------------------------------------+
# | Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
# | This program is free software: you can redistribute it and/or modify      |
# | it under the terms of the GNU General Public License as published by      |
# | the Free Software Foundation, either version 3 of the License, or         |
# | (at your option) any later version.                                       |
# |                                                                           |
# | This program is distributed in the hope that it will be useful,           |
# | but WITHOUT ANY WARRANTY; without even the implied warranty of            |
# | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
# | GNU General Public License for more details.                              |
# |                                                                           |
# | You should have received a copy of the GNU General Public License         |
# | along with this program. If not, see <http://www.gnu.org/licenses/>.      |
# +---------------------------------------------------------------------------+
# | @url      : http://www.netzob.org                                         |
# | @contact  : contact@netzob.org                                            |
# | @sponsors : Amossys, http://www.amossys.fr                                |
# |             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | File contributors :                                                       |
# |       - Georges Bossert <georges.bossert (a) supelec.fr>                  |
# |       - Frédéric Guihéry <frederic.guihery (a) amossys.fr>                |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Standard library imports                                                  |
# +---------------------------------------------------------------------------+
import random
import os
from bitarray import bitarray
from enum import Enum

# +---------------------------------------------------------------------------+
# | Related third party imports                                               |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Local application imports                                                 |
# +---------------------------------------------------------------------------+
from netzob.Model.Vocabulary.Types.AbstractType import AbstractType


class Raw(AbstractType):
    """Raw netzob data type expressed in bytes.

    For instance, we can use this type to parse any raw field of 2 bytes:

    >>> from netzob.all import *
    >>> f = Field(Raw(nbBytes=2))

    or with a specific value (default is little endianness)

    >>> f = Field(Raw('\\x01\\x02\\x03'))
    >>> print(f.domain.dataType)
    Raw=b'\\x01\\x02\\x03' ((0, 24))

    >>> f.domain.dataType.endianness = AbstractType.ENDIAN_BIG
    >>> print(f.domain.dataType)
    Raw=b'\\x01\\x02\\x03' ((0, 24))

    The alphabet optional argument can be use to limit the bytes that can participate in the domain value

    >>> f = Field(Raw(nbBytes=100, alphabet=["t", "o"]))
    >>> data = f.specialize()
    >>> data_set = set(data)
    >>> print(data_set)
    {116, 111}

    """

    def __init__(self,
                 value=None,
                 nbBytes=None,
                 unitSize=AbstractType.defaultUnitSize(),
                 endianness=AbstractType.defaultEndianness(),
                 sign=AbstractType.defaultSign(),
                 alphabet=None):
        if value is not None and not isinstance(value, bitarray):
            from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
            from netzob.Model.Vocabulary.Types.BitArray import BitArray
            if isinstance(value, str):
                value = TypeConverter.convert(
                    bytes(value, "utf-8"), Raw, BitArray)
            elif isinstance(value, bytes):
                value = TypeConverter.convert(value, Raw, BitArray)

        nbBits = self._convertNbBytesinNbBits(nbBytes)

        self.alphabet = alphabet
        
        super(Raw, self).__init__(
            self.__class__.__name__,
            value,
            nbBits,
            unitSize=unitSize,
            endianness=endianness,
            sign=sign)

    def __str__(self):
        if self.value is not None:
            from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
            from netzob.Model.Vocabulary.Types.BitArray import BitArray
            from netzob.Model.Vocabulary.Types.HexaString import HexaString
            return "{0}={1} ({2})".format(
                self.typeName,
                repr(TypeConverter.convert(self.value, BitArray, Raw)),
                self.size)
        else:
            return "{0}={1} ({2})".format(self.typeName, self.value, self.size)

    def __repr__(self):
        """
        >>> from netzob.all import *
        >>> f = Field(Raw("\\x01\\x02\\x03\\x04"))
        >>> s = Symbol(fields=[f])
        >>> messages = [RawMessage(s.specialize()) for x in range(5)]
        >>> s.messages = messages
        >>> print(s)
        Field             
        ------------------
        '\\x01\\x02\\x03\\x04'
        '\\x01\\x02\\x03\\x04'
        '\\x01\\x02\\x03\\x04'
        '\\x01\\x02\\x03\\x04'
        '\\x01\\x02\\x03\\x04'
        ------------------

        """
        if self.value is not None:
            from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
            from netzob.Model.Vocabulary.Types.BitArray import BitArray
            return str(
                TypeConverter.convert(self.value, BitArray, self.__class__))
        else:
            return str(self.value)

    def _convertNbBytesinNbBits(self, nbBytes):
        nbMinBit = None
        nbMaxBit = None
        if nbBytes is not None:
            if isinstance(nbBytes, int):
                nbMinBit = nbBytes * 8
                nbMaxBit = nbMinBit
            else:
                if nbBytes[0] is not None:
                    nbMinBit = nbBytes[0] * 8
                if nbBytes[1] is not None:
                    nbMaxBit = nbBytes[1] * 8
        return (nbMinBit, nbMaxBit)

    def generate(self, generationStrategy=None):
        """Generates a random Raw that respects the requested size.

        >>> from netzob.all import *
        >>> a = Raw(nbBytes=(10))
        >>> gen = a.generate()
        >>> print(len(gen))
        80

        >>> from netzob.all import *
        >>> a = Raw(nbBytes=(10, 20))
        >>> gen = a.generate()
        >>> print(10<=len(gen) and 20<=len(gen))
        True



        """
        from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
        from netzob.Model.Vocabulary.Types.BitArray import BitArray

        minSize, maxSize = self.size
        if maxSize is None:
            maxSize = AbstractType.MAXIMUM_GENERATED_DATA_SIZE
        if minSize is None:
            minSize = 0

        generatedSize = random.randint(minSize, maxSize)

        generatedValue = None
        if self.alphabet is None:
            generatedValue = os.urandom(int(generatedSize / 8))
        else:
            generatedValue = "".join([random.choice(self.alphabet) for _ in range(int(generatedSize / 8))])
            
        return TypeConverter.convert(generatedValue, Raw, BitArray)

    @staticmethod
    def decode(data,
               unitSize=AbstractType.defaultUnitSize(),
               endianness=AbstractType.defaultEndianness(),
               sign=AbstractType.defaultSign()):
        return data

    @staticmethod
    def encode(data,
               unitSize=AbstractType.defaultUnitSize(),
               endianness=AbstractType.defaultEndianness(),
               sign=AbstractType.defaultSign()):
        return data

    def canParse(self, data,
                 unitSize=AbstractType.defaultUnitSize(),
                 endianness=AbstractType.defaultEndianness(),
                 sign=AbstractType.defaultSign()):
        """Computes if specified data can be parsed as raw which is always the case if the data is at least 1 length and aligned on a byte.

        >>> from netzob.all import *
        >>> Raw().canParse(TypeConverter.convert("hello netzob", ASCII, BitArray))
        True

        The ascii table is defined from 0 to 127:
        >>> Raw().canParse(TypeConverter.convert(128, Integer, BitArray, src_sign=AbstractType.SIGN_UNSIGNED))
        True

        :param data: the data to check
        :type data: python raw
        :return: True if data can be parsed as a Raw which is always the case (if len(data)>0)
        :rtype: bool
        :raise: TypeError if the data is None
        """

        if data is None:
            raise TypeError("data cannot be None")

        if len(data) == 0:
            return False

        if len(data) % 8 != 0:
            return False

        if self.alphabet is not None:
            data_set = set(data)
            for element in data_set:
                if element not in self.alphabet:
                    return False

        return True

    def _construct_boundary_values(self):
        bounds = super(Raw, self)._construct_boundary_values(align=(self.alphabet is not None))
        min_size, max_size = self.size
        omit = [] # Boundary values that shall be omitted
        if self.alphabet is not None:
            omit.append('VALUE_NONE')
            omit.append('VALUE_ALL')
            omit.append('VALUE_RAND')
            omit.append('VALUE_MSB')
            omit.append('VALUE_LSB')
            omit.append('VALUE_TOPHALF')
            omit.append('VALUE_BOTTOMHALF')
            if max_size < 2*self.unit_size_to_int(self.unitSize):
                omit.append('VALUE_ILLEGAL_END')
            if max_size < 3*self.unit_size_to_int(self.unitSize):
                omit.append('VALUE_ILLEGAL_RAND')
        else:
            omit.append('VALUE_LEGAL')
            omit.append('VALUE_ILLEGAL_START')
            omit.append('VALUE_ILLEGAL_END')
            omit.append('VALUE_ILLEGAL_RAND')
            if max_size < 4:
                omit.append('VALUE_TOPHALF')
            if max_size < 3:
                omit.append('VALUE_BOTTOMHALF')
                omit.append('VALUE_RAND')
            if max_size < 2:
                omit.append('VALUE_MSB')
                omit.append('VALUE_LSB')
        bounds[Raw.BoundaryValue.__name__] = [x for x in Raw.BoundaryValue.__members__ if x not in omit]
        return bounds

    class BoundaryValue(Enum):
        VALUE_NONE = ('VALUE_NONE', True)
        VALUE_ALL = ('VALUE_ALL', True)
        VALUE_RAND = ('VALUE_RAND', True)
        VALUE_MSB = ('VALUE_MSB', True)
        VALUE_LSB = ('VALUE_LSB', True)
        VALUE_TOPHALF = ('VALUE_TOPHALF', True)
        VALUE_BOTTOMHALF = ('VALUE_BOTTOMHALF', True)
        VALUE_LEGAL = ('VALUE_LEGAL', True)
        VALUE_ILLEGAL_START = ('VALUE_ILLEGAL_START', False)
        VALUE_ILLEGAL_END = ('VALUE_ILLEGAL_END', False)
        VALUE_ILLEGAL_RAND = ('VALUE_ILLEGAL_RAND', False)

        ''' Returns False if this is a negative (invalid) value, True otherwise '''
        def __bool__(self):
            return self.value[1]

    def concretize(self, ca_values):
        size = super(Raw, self).concretize(ca_values, align=(self.alphabet is not None))

        if Raw.BoundaryValue.__name__ in ca_values:
            val = Raw.BoundaryValue[ca_values[Raw.BoundaryValue.__name__]]
            value = bitarray(size, endian=self.endianness)

            if val == Raw.BoundaryValue.VALUE_NONE:
                value.setall(0)
            elif val == Raw.BoundaryValue.VALUE_ALL:
                value.setall(1)
            elif val == Raw.BoundaryValue.VALUE_MSB:
                value.setall(0)
                value[0] = 1
            elif val == Raw.BoundaryValue.VALUE_LSB:
                value.setall(0)
                value[-1] = 1
            elif val == Raw.BoundaryValue.VALUE_TOPHALF:
                value.setall(0)
                value[0:int(size/2)] = 1
            elif val == Raw.BoundaryValue.VALUE_BOTTOMHALF:
                value.setall(0)
                value[int(size/2):] = 1
            elif val == Raw.BoundaryValue.VALUE_RAND:
                excluded = [bitarray(size, endian=self.endianness)
                            , bitarray(size, endian=self.endianness)
                            , bitarray(size, endian=self.endianness)
                            , bitarray(size, endian=self.endianness)
                            , bitarray(size, endian=self.endianness)
                            , bitarray(size, endian=self.endianness)
                            ]
                excluded[0].setall(0)
                excluded[1].setall(1)
                excluded[2].setall(0)
                excluded[2][0] = 1
                excluded[3].setall(0)
                excluded[3][-1] = 1
                excluded[4].setall(0)
                excluded[4][0:int(size/2)] = 1
                excluded[5].setall(0)
                excluded[5][int(size/2):] = 1
                randomContent = [random.randint(0, 1) for i in range(0, size)]
                value = bitarray(randomContent, endian=self.endianness)
                while value in excluded:
                    randomContent = [random.randint(0, 1) for i in range(0, size)]
                    value = bitarray(randomContent, endian=self.endianness)
            elif val == Raw.BoundaryValue.VALUE_LEGAL:
                assert self.alphabet is not None
                generated = "".join([random.choice(self.alphabet) for _ in range(int(size / 8))])
                from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
                from netzob.Model.Vocabulary.Types.BitArray import BitArray
                value = TypeConverter.convert(generated, Raw, BitArray)
            elif val == Raw.BoundaryValue.VALUE_ILLEGAL_START \
                 or val == Raw.BoundaryValue.VALUE_ILLEGAL_END \
                 or val == Raw.BoundaryValue.VALUE_ILLEGAL_RAND:
                assert self.alphabet is not None
                # Really dumb special case that allows all characters
                assert len(self.alphabet) < 128
                badbyte = chr(random.randint(0, 127))
                len_bytes = int(size / 8)
                while badbyte in self.alphabet:
                    badbyte = chr(random.randint(0, 127))
                if val == Raw.BoundaryValue.VALUE_ILLEGAL_START:
                    generated = str(badbyte) + "".join([random.choice(self.alphabet) for _ in range(len_bytes-1)])
                elif val == Raw.BoundaryValue.VALUE_ILLEGAL_END:
                    generated = "".join([random.choice(self.alphabet) for _ in range(len_bytes-1)]) + str(badbyte)
                elif val == Raw.BoundaryValue.VALUE_ILLEGAL_RAND:
                    prefix_len = random.randint(1, len_bytes-2)
                    generated = "".join([random.choice(self.alphabet) for _ in range(prefix_len)])
                    generated += badbyte
                    generated += "".join([random.choice(self.alphabet) for _ in range(len_bytes-prefix_len-1)])
                from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
                from netzob.Model.Vocabulary.Types.BitArray import BitArray
                value = TypeConverter.convert(generated, Raw, BitArray)

            self.value = value
            return self

        raise ValueError('Could not construct Raw, no valid spec in CA')
