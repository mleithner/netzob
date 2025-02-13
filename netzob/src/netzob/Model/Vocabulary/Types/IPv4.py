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
import struct
import random
from enum import Enum

# +---------------------------------------------------------------------------+
# | Related third party imports                                               |
# +---------------------------------------------------------------------------+
from netaddr import IPAddress, IPNetwork
from bitarray import bitarray

# +---------------------------------------------------------------------------+
# | Local application imports                                                 |
# +---------------------------------------------------------------------------+
from netzob.Common.Utils.Decorators import NetzobLogger
from netzob.Model.Vocabulary.Types.AbstractType import AbstractType


@NetzobLogger
class IPv4(AbstractType):
    """This class supports the definition of type IPv4 in Netzob.
    it defines how to encode a python raw in an IPv4 representation or in the other way, to
    decode an IPv4 into a Raw.

    This type can be used to define which IPv4 is expected as a domain:

    >>> from netzob.all import *
    >>> ip = IPv4("192.168.0.10")
    >>> ip.size
    (32, 32)
    >>> ip.value
    bitarray('11000000101010000000000000001010')

    >>> f1 = Field("IP=")
    >>> f2 = Field(IPv4())
    >>> s = Symbol(fields=[f1,f2])
    >>> msgs = [RawMessage(s.specialize()) for x in range(10)]
    >>> print(len(msgs))
    10

    """

    def __init__(self,
                 value=None,
                 network=None,
                 unitSize=AbstractType.defaultUnitSize(),
                 endianness=AbstractType.defaultEndianness(),
                 sign=AbstractType.defaultSign()):
        """Builds an IPv4 domain with optional constraints.

        :parameter value: specify a constraints over the expected value.
        :type value: an str, an IPAddress or an int which can be parsed as an IPv4 (ex. "192.168.0.10")
        :parameter network: if no value is specified (None), a constraints over the network the parsed IP belongs can be specified with this parameter (ex. "192.168.0.0/24")
        :type network: an str or an IPAddress which can be parsed as a network IPv4
        """

        if value is not None and not isinstance(value, bitarray):
            from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
            from netzob.Model.Vocabulary.Types.BitArray import BitArray
            value = TypeConverter.convert(
                value,
                IPv4,
                BitArray,
                src_unitSize=unitSize,
                src_endianness=endianness,
                src_sign=sign,
                dst_unitSize=unitSize,
                dst_endianness=endianness,
                dst_sign=sign)

        self.network = network

        super(IPv4, self).__init__(
            self.__class__.__name__,
            value,
            32,
            unitSize=unitSize,
            endianness=endianness,
            sign=sign)

    def generate(self, generationStrategy=None):
        """Generates a random IPv4 which follows the constraints.

        >>> from netzob.all import *
        >>> f = Field(IPv4())
        >>> len(f.specialize())
        4

        >>> f = Field(IPv4("192.168.0.10"))
        >>> TypeConverter.convert(f.specialize(), Raw, IPv4)
        IPAddress('192.168.0.10')

        >>> f = Field(IPv4(network="10.10.10.0/24"))
        >>> TypeConverter.convert(f.specialize(), Raw, IPv4) in IPNetwork("10.10.10.0/24")
        True

        """
        from netzob.Model.Vocabulary.Types.BitArray import BitArray
        from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
        from netzob.Model.Vocabulary.Types.Raw import Raw

        if self.value is not None:
            return self.value
        elif self.network is not None:
            ip = random.choice(self.network)
            return TypeConverter.convert(
                ip.packed,
                Raw,
                BitArray,
                src_unitSize=self.unitSize,
                src_endianness=self.endianness,
                src_sign=self.sign,
                dst_unitSize=self.unitSize,
                dst_endianness=self.endianness,
                dst_sign=self.sign)
        else:
            not_valid = [10, 127, 169, 172, 192]

            first = random.randrange(1, 256)
            while first in not_valid:
                first = random.randrange(1, 256)

            strip = ".".join([
                str(first), str(random.randrange(1, 256)),
                str(random.randrange(1, 256)), str(random.randrange(1, 256))
            ])

            ip = IPv4.encode(strip)
            return TypeConverter.convert(
                ip.packed,
                Raw,
                BitArray,
                src_unitSize=self.unitSize,
                src_endianness=self.endianness,
                src_sign=self.sign,
                dst_unitSize=self.unitSize,
                dst_endianness=self.endianness,
                dst_sign=self.sign)

    def canParse(self,
                 data,
                 unitSize=AbstractType.defaultUnitSize(),
                 endianness=AbstractType.defaultEndianness(),
                 sign=AbstractType.defaultSign()):
        """Computes if specified data can be parsed as an IPv4 with the predefined constraints.

        >>> from netzob.all import *
        >>> ip = IPv4()
        >>> ip.canParse("192.168.0.10")
        True
        >>> ip.canParse("198.128.0.100")
        True
        >>> ip.canParse("256.0.0.1")
        False
        >>> ip.canParse("127.0.0.1")
        True
        >>> ip.canParse("127.0.0.-1")
        False
        >>> ip.canParse("::")
        False
        >>> ip.canParse("0.0.0.0")
        False


        And with some constraints over the expected IPv4:


        >>> ip = IPv4("192.168.0.10")
        >>> ip.canParse("192.168.0.10")
        True
        >>> ip.canParse("192.168.1.10")
        False
        >>> ip.canParse(3232235530)
        True
        >>> ip = IPv4("167.20.14.20")
        >>> ip.canParse(3232235530)
        False
        >>> ip.canParse(3232235530)
        False


        or with contraints over the expected network the ipv4 belongs to:


        >>> ip = IPv4(network="192.168.0.0/24")
        >>> ip.canParse("192.168.0.10")
        True
        >>> ip.canParse("192.168.1.10")
        False

        :param data: the data to check
        :type data: python raw
        :return: True if data can be parsed as a Raw which is always the case (if len(data)>0)
        :rtype: bool
        :raise: TypeError if the data is None
        """

        if data is None:
            raise TypeError("data cannot be None")

        try:
            ip = IPv4.encode(
                data, unitSize=unitSize, endianness=endianness, sign=sign)
            if ip is None or ip.version != 4 or ip.is_netmask():
                return False
        except:
            return False
        try:
            if self.value is not None:
                from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
                from netzob.Model.Vocabulary.Types.BitArray import BitArray
                return self.value == TypeConverter.convert(
                    data,
                    IPv4,
                    BitArray,
                    src_unitSize=unitSize,
                    src_endianness=endianness,
                    src_sign=sign,
                    dst_unitSize=self.unitSize,
                    dst_endianness=self.endianness,
                    dst_sign=self.sign)
            elif self.network is not None:
                return ip in self.network
        except:
            return False

        return True

    def _isValidIPv4Network(self, network):
        """Computes if the specified network is a valid IPv4 network.

        >>> from netzob.all import *
        >>> ip = IPv4()
        >>> ip._isValidIPv4Network("192.168.0.10")
        True
        >>> ip._isValidIPv4Network("-1.168.0.10")
        False

        """
        if network is None:
            raise TypeError("None is not valid IPv4 network")
        try:
            net = IPNetwork(network)
            if net is not None and net.version == 4:
                return True
        except:
            return False
        return False

    @property
    def network(self):
        """A constraint over the network the parsed data belongs to this network or not."""
        return self.__network

    @network.setter
    def network(self, network):
        if network is not None:
            if not self._isValidIPv4Network(network):
                raise TypeError(
                    "Specified network constraints is not valid IPv4 Network.")
            self.__network = IPNetwork(network)
        else:
            self.__network = None

    @staticmethod
    def decode(data,
               unitSize=AbstractType.defaultUnitSize(),
               endianness=AbstractType.defaultEndianness(),
               sign=AbstractType.defaultSign()):
        """Decode the specified IPv4 data into its raw representation.

        >>> from netzob.all import *
        >>> print(IPv4.decode("127.0.0.1"))
        b'\\x7f\\x00\\x00\\x01'

        """

        if data is None:
            raise TypeError("Data cannot be None")
        ip = IPv4()
        if not ip.canParse(data):
            raise TypeError("Data is not a valid IPv4, cannot decode it.")
        ip = IPAddress(data)
        return ip.packed

    @staticmethod
    def encode(data,
               unitSize=AbstractType.defaultUnitSize(),
               endianness=AbstractType.defaultEndianness(),
               sign=AbstractType.SIGN_UNSIGNED):
        """Encodes the specified data into an IPAddress object

        :param data: the data to encode into an IPAddress
        :type data: str or raw bytes (BBBB)
        :return: the encoded IPAddress
        """
        if isinstance(data, (str, int)):
            try:
                ip = IPAddress(data)
                if ip is not None and ip.version == 4 and not ip.is_netmask():
                    return ip
            except:
                pass
        try:

            structFormat = "<"
            if endianness == AbstractType.ENDIAN_BIG:
                structFormat = ">"

            if sign is AbstractType.SIGN_SIGNED:
                structFormat += "bbbb"
            else:
                structFormat += "BBBB"
            quads = list(map(str, struct.unpack(structFormat, data)))
            strIP = '.'.join(quads)

            ip = IPAddress(strIP)
            if ip is not None and ip.version == 4 and not ip.is_netmask():
                return ip
        except Exception as e:
            raise TypeError("Impossible encode {0} into an IPv4 data ({1})".
                            format(data, e))

    def _construct_boundary_values(self):
        bounds = super(IPv4, self)._construct_boundary_values(align=False)
        omit = [] # Boundary values that shall be omitted
        if self.network is not None:
            omit.append('VALUE_LOCALHOST')
            omit.append('VALUE_PRIVATE')
            omit.append('VALUE_LINK')
            omit.append('VALUE_TESTNET')
            omit.append('VALUE_6TO4')
            omit.append('VALUE_MULTICAST')
            omit.append('VALUE_RESERVED')
            omit.append('VALUE_PUBLIC')
        else:
            omit.append('VALUE_HOST')
            omit.append('VALUE_BROADCAST')
            omit.append('VALUE_NET')
            omit.append('VALUE_ILLEGAL')
        bounds[IPv4.BoundaryValue.__name__] = [IPv4.BoundaryValue[x].value for x in IPv4.BoundaryValue.__members__ if x not in omit]
        return bounds

    class BoundaryValue(Enum):
        VALUE_HOST = ('VALUE_HOST', True)
        VALUE_BROADCAST = ('VALUE_BROADCAST', False)
        VALUE_NET = ('VALUE_NET', False)
        VALUE_ILLEGAL = ('VALUE_ILLEGAL', False)
        VALUE_LOCALHOST = ('VALUE_LOCALHOST', True)
        VALUE_PRIVATE = ('VALUE_PRIVATE', True)
        VALUE_LINK = ('VALUE_LINK', False)
        VALUE_TESTNET = ('VALUE_TESTNET', True)
        VALUE_6TO4 = ('VALUE_6TO4', False)
        VALUE_MULTICAST = ('VALUE_MULTICAST', False)
        VALUE_RESERVED = ('VALUE_RESERVED', False)
        VALUE_PUBLIC = ('VALUE_PUBLIC', True)

        ''' Returns False if this is a negative (invalid) value, True otherwise '''
        def __bool__(self):
            return self.value[1]

    def concretize(self, ca_values):
        if IPv4.BoundaryValue.__name__ in ca_values:
            import string
            val = IPv4.BoundaryValue[ca_values[IPv4.BoundaryValue.__name__]]

            if val == IPv4.BoundaryValue.VALUE_HOST or val == IPv4.BoundaryValue.VALUE_NET \
               or val == IPv4.BoundaryValue.VALUE_ILLEGAL:
                # We need a defined network to compute these
                assert self.network is not None

                if val == IPv4.BoundaryValue.VALUE_HOST:
                    value = random.choice([ip for ip in self.network.iter_hosts()])
                elif val == IPv4.BoundaryValue.VALUE_NET:
                    value = self.network.network
                elif val == IPv4.BoundaryValue.VALUE_ILLEGAL:
                    value = random.choice([ip for ip in self.network.next().iter_hosts()])

            elif val == IPv4.BoundaryValue.VALUE_LOCALHOST:
                value = IPAddress('127.0.0.1')
            elif val == IPv4.BoundaryValue.VALUE_PRIVATE:
                # Fixed to one network for now because it takes a second or two
                # to pick a random address from larger ranges
                value = random.choice([ip for ip in IPNetwork('192.168.0.0/16').iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_LINK:
                value = random.choice([ip for ip in IPNetwork('169.254.0.0/16').iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_TESTNET:
                net = random.choice([IPNetwork('192.0.2.0/24')
                                    , IPNetwork('198.51.100.0/24')
                                    , IPNetwork('203.0.113.0/24')])
                value = random.choice([ip for ip in net.iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_6TO4:
                value = random.choice([ip for ip in IPNetwork('192.88.99.0/24').iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_MULTICAST:
                # Restricted from /4 to /16 for performance reasons
                value = random.choice([ip for ip in IPNetwork('224.0.0.0/16').iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_RESERVED:
                # Restricted from /4 to /16 for performance reasons
                value = random.choice([ip for ip in IPNetwork('240.0.0.0/16').iter_hosts()])
            elif val == IPv4.BoundaryValue.VALUE_BROADCAST:
                if self.network is not None:
                    value = self.network.broadcast
                else:
                    value = IPAddress('255.255.255.255')
            elif val == IPv4.BoundaryValue.VALUE_PUBLIC:
                # Just using a fixed network for now...
                value = random.choice([ip for ip in IPNetwork('13.37.0.0/16').iter_hosts()])

            from netzob.Model.Vocabulary.Types.BitArray import BitArray
            from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter
            from netzob.Model.Vocabulary.Types.Raw import Raw

            value = TypeConverter.convert(
                value.packed,
                Raw,
                BitArray,
                src_unitSize=self.unitSize,
                src_endianness=self.endianness,
                src_sign=self.sign,
                dst_unitSize=self.unitSize,
                dst_endianness=self.endianness,
                dst_sign=self.sign)

            self.value = value
            self.concretized = True
            return self

        raise ValueError('Could not construct IPv4, no valid spec in CA')
