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
# |             ANSSI,   https://www.ssi.gouv.fr                              |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | File contributors :                                                       |
# |       - Georges Bossert <georges.bossert (a) supelec.fr>                  |
# |       - Frédéric Guihéry <frederic.guihery (a) amossys.fr>                |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Standard library imports                                                  |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Related third party imports                                               |
# +---------------------------------------------------------------------------+
from bitarray import bitarray

# +---------------------------------------------------------------------------+
# | Local application imports                                                 |
# +---------------------------------------------------------------------------+
from netzob.Common.Utils.Decorators import NetzobLogger
from netzob.Common.Utils.Decorators import typeCheck
from netzob.Model.Vocabulary.AbstractField import AbstractField
from netzob.Model.Vocabulary.Domain.Variables.AbstractVariable import AbstractVariable
from netzob.Model.Vocabulary.Types.AbstractType import AbstractType
from netzob.Common.Utils.TypedList import TypedList
from netzob.Model.Vocabulary.Messages.AbstractMessage import AbstractMessage
from netzob.Model.Vocabulary.Field import Field
from netzob.Model.Vocabulary.Domain.Variables.Memory import Memory
from netzob.Model.Vocabulary.Types.Raw import Raw
from netzob.Model.Vocabulary.Types.BitArray import BitArray
from netzob.Model.Vocabulary.Types.TypeConverter import TypeConverter


class Symbol(AbstractField):
    """A symbol represents a common abstraction for all its messages.

    For example, we can create a symbol based on two raw messages

    >>> from netzob.all import *
    >>> m1 = RawMessage("hello world")
    >>> m2 = RawMessage("hello earth")
    >>> fields = [Field("hello ", name="f0"), Field(["world", "earth"], name="f1")]
    >>> symbol = Symbol(fields, messages=[m1, m2])
    >>> print(symbol)
    f0       | f1     
    -------- | -------
    'hello ' | 'world'
    'hello ' | 'earth'
    -------- | -------

    Another example
    
    >>> from netzob.all import *
    >>> s = Symbol([Field("hello ", name="f0"), Field(ASCII(nbChars=(0, 10)), name="f1")])
    >>> s.messages.append(RawMessage("hello toto"))
    >>> print(s)
    f0       | f1    
    -------- | ------
    'hello ' | 'toto'
    -------- | ------

    """

    def __init__(self, fields=None, messages=None, name="Symbol", meta=False):
        """
        :keyword fields: the fields which participate in symbol definition
        :type fields: a :class:`list` of :class:`netzob.Model.Vocabulary.Field`
        :keyword messages: the message that represent the symbol
        :type messages: a :class:`list` of :class:`netzob.Model.Vocabulary.Messages.AbstractMessage.AbstractMessage`
        :keyword name: the name of the symbol
        :type name: :class:`str`
        """
        super(Symbol, self).__init__(name,meta)
        self.__messages = TypedList(AbstractMessage)
        if messages is None:
            messages = []
        self.messages = messages
        if fields is None:
            # create a default empty field
            fields = [Field()]
        self.fields = fields

    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return False
        if other is None:
            return False
        return self.name == other.name

    def __ne__(self, other):
        if other is None:
            return True
        if not isinstance(other, Symbol):
            return True
        return other.name != self.name

    def __key(self):
        return self.id

    def __hash__(self):
        return hash(self.id)

    @typeCheck(Memory, object)
    def specialize(self, memory=None, generationStrategy=None, presets=None):
        """Specialize and generate an hexastring which content
        follows the fields definitions attached to the field of the symbol.

        >>> from netzob.all import *
        >>> f1 = Field(domain=ASCII(nbChars=5))
        >>> f0 = Field(domain=Size(f1))
        >>> s = Symbol(fields=[f0, f1])
        >>> result = s.specialize()
        >>> print(result[0])
        5
        >>> print(len(result))
        6

        You can also preset the value of some variables included in the symbol definition.

        >>> from netzob.all import *
        >>> f1 = Field(domain=ASCII("hello "))
        >>> f2 = Field(domain=ASCII(nbChars=(1,10)))
        >>> s = Symbol(fields = [f1, f2])
        >>> presetValues = dict()
        >>> presetValues[f2] = TypeConverter.convert("antoine", ASCII, BitArray)
        >>> print(s.specialize(presets = presetValues))
        b'hello antoine'

        A preseted valued bypasses all the constraints checks on your field definition.
        For example, in the following example it can be use to bypass a size field definition.

        >>> from netzob.all import *
        >>> f1 = Field()
        >>> f2 = Field(domain=Raw(nbBytes=(10,15)))
        >>> f1.domain = Size(f2)
        >>> s = Symbol(fields=[f1, f2])
        >>> presetValues = {f1: TypeConverter.convert("\xff", Raw, BitArray)}        
        >>> print(s.specialize(presets = presetValues)[0])
        195

        :keyword generationStrategy: if set, the strategy will be used to generate the fields definitions
        :type generaionrStrategy: :class:``

        :return: a generated content represented as a Raw
        :rtype: :class:`str``
        :raises: :class:`netzob.Model.Vocabulary.AbstractField.GenerationException` if an error occurs while generating a message
        """

        from netzob.Model.Vocabulary.Domain.Specializer.MessageSpecializer import MessageSpecializer
        msg = MessageSpecializer(memory=memory, presets=presets)
        spePath = msg.specializeSymbol(self)

        if spePath is not None:
            return TypeConverter.convert(spePath.generatedContent, BitArray,
                                         Raw)

    def specialize_from_ca(self, path, ca_format='pict', ipm=None, memory=None, presets=None):
        """Returns a list of specialized messages as raw data, based on the contents
        of a CA given as `path`.

        Note that currently, the entire CA is read into memory.
        This might be ill-advised for very large CAs; in this case,
        it would be better to implement windowed buffering (which is
        somewhat complex due to the semantics of Alt/Repeat variables).

        The IPM must have been created using Symbel.build_ipm(); if it is
        not specified, it will be recreated.
        """

        if ipm is None:
            ipm = self.build_ipm(None, memory=memory, presets=presets, ipm_format=None)

        print('Specializing CA using IPM:')
        print(ipm)
        (ca_parameters, ca_rows) = Symbol.read_ca(path, ca_format)
        print(ca_parameters)
        print(f'Have {len(ca_rows)} rows in CA')
        #print(ca_rows)

        # Let's set up a mapping to quickly retrieve the right columns
        type_columns = []
        variable_columns = []
        for ipm_key in ipm:
            if isinstance(ipm[ipm_key], (AbstractVariable, AbstractType)):
                if isinstance(ipm[ipm_key], AbstractVariable):
                    print(f'Parameter {ipm_key} is a variable')
                    param_prefix = f'{ipm_key}_{AbstractVariable.IPM_PARAMS_PREFIX}_'
                elif isinstance(ipm[ipm_key], AbstractType):
                    print(f'Parameter {ipm_key} is a primitive type')
                    param_prefix = f'{ipm_key}_{AbstractType.IPM_PARAMS_PREFIX}_'
                # Only those CA columns that pertain to this type
                type_params = filter(lambda e: e[1].startswith(param_prefix), enumerate(ca_parameters))
                # Strip the prefix and assign the (column, name) tuple
                params = []
                for (column_idx, param_name) in map(lambda s: (s[0], s[1].removeprefix(param_prefix)), type_params):
                    print(f'Assigning column {column_idx} to parameter {param_name} for {ipm_key}')
                    params.append((column_idx, param_name))

                if isinstance(ipm[ipm_key], AbstractVariable):
                    variable_columns.append({'object': ipm[ipm_key], 'params': params})
                elif isinstance(ipm[ipm_key], AbstractType):
                    type_columns.append({'object': ipm[ipm_key], 'params': params})

        print(type_columns)
        print(variable_columns)

        for row in ca_rows:
            print(f'Concretizing row {row}')

            for t_col in type_columns:
                type_values = {}
                for (column_idx, param_name) in t_col['params']:
                    type_values[param_name] = row[column_idx]
                t_col['object'].concretize(type_values)
                print(t_col['object'].value)

            print('BREAK')
            break



    @staticmethod
    def read_ca(path, ca_format):
        import csv
        parameters = []
        rows = []
        if ca_format == 'pict':
            with open(path, newline='') as ca_file:
                reader = csv.reader(ca_file, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    if not parameters:
                        parameters = row
                    else:
                        rows.append(row)
            return (parameters, rows)

        # Not a valid format
        raise ValueError('CA format unsupported.')


    def build_ipm(self, path, memory=None, presets=None, ipm_format='pict'):
        """Constructs an IPM for this symbol.
        An input parameter model defines the parameters and their respective
        values to be used in combinatorial testing.
        This method first gathers all the parameters required to represent
        the fields of this message in a tree-like structure and then outputs
        an IPM to the `path`, which should be a path to a non-existent file."""

        from netzob.Model.Vocabulary.Domain.Specializer.MessageSpecializer import MessageSpecializer
        msg = MessageSpecializer(memory=memory, presets=presets)
        ipm = msg.build_ipm(self)
        self._logger.debug('Dumping intermediate IPM:')
        self._logger.debug(ipm)

        ipm_columns = {}
        for field in ipm:
            ipm_columns.update(Symbol.flatten_ipm_params(ipm[field], f'{self.name}_{field}'))
        self._logger.debug('Dumping intermediate IPM columns:')
        self._logger.debug(ipm_columns)

        if ipm_format is None:
            return ipm_columns
        if ipm_format == 'pict':
            self._logger.debug(f'Writing IPM as PICT input file to {path}')
            return Symbol.output_ipm_pict(ipm_columns, path)

        # No valid output format
        raise ValueError(f'Output ipm_format "{ipm_format}" is unsupported.')

    # XXX Do we even want this?
    @typeCheck(Memory, object)
    def generate_ca_pict(self, pict_path, path, strength=2, memory=None, presets=None):
        self.build_ipm(path, memory, presets, format='pict')
        from subprocess import Popen, PIPE, TimeoutExpired
        print(f'Will try to generate CA using PICT at {pict_path} with generated input file {path} and t={strength}')
        proc = Popen([pict_path, path, f'/o:{strength}'], stdout=PIPE, stderr=PIPE, text=True, encoding='utf-8')
        print('Process created, waiting for output...')
        try:
            outs, errs = proc.communicate()
            # XXX TODO
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            # XXX TODO

    @staticmethod
    def flatten_ipm_params(field_ipm, prefix):
        field_columns = {}
        if field_ipm['domain']:
            field_columns.update(Symbol._ipm_domain_rec(field_ipm['domain'], f'{prefix}'))

        for child in field_ipm['children']:
            field_columns.update(Symbol.flatten_ipm_params(field_ipm['children'][child], f'{prefix}_{child}'))

        return field_columns

    @staticmethod
    def _ipm_domain_rec(domain, prefix):
        field_columns = {}
        for param in domain:
            if isinstance(domain[param], dict):
                field_columns.update(Symbol._ipm_domain_rec(domain[param], f'{prefix}_{param}'))
            elif isinstance(domain[param], list):
                field_columns[f'{prefix}_{param}'] = domain[param]
            elif isinstance(domain[param], (AbstractType, AbstractVariable)):
                field_columns[prefix] = domain[param]
        return field_columns


    @staticmethod
    def output_ipm_pict(ipm_columns, path):
        with open(path, 'w', encoding='utf-8') as ipm_file:
            for param in ipm_columns:
                if isinstance(ipm_columns[param], list):
                    line = f'{param}: {Symbol.format_ipm_values(ipm_columns[param])}\n'
                    ipm_file.write(line)

    @staticmethod
    def format_ipm_values(ipm_column):
        return ','.join(map(lambda c: f'{"" if c[1] else "~"}{c[0]}', ipm_column))


    def clearMessages(self):
        """Delete all the messages attached to the current symbol"""
        while (len(self.__messages) > 0):
            self.__messages.pop()

    # Properties

    @property
    def messages(self):
        """A list containing all the messages that this symbol represent.

        :type : a :class:`list` of :class:`netzob.Model.Vocabulary.Messages.AbstractMessage.AbstractMessage`
        """
        return self.__messages

    @messages.setter
    def messages(self, messages):
        if messages is None:
            messages = []

        # First it checks the specified messages are all AbstractMessages
        for msg in messages:
            if not isinstance(msg, AbstractMessage):
                raise TypeError(
                    "Cannot add messages of type {0} in the session, only AbstractMessages are allowed.".
                    format(type(msg)))

        self.clearMessages()
        for msg in messages:
            self.__messages.append(msg)

    def __repr__(self):
        return self.name
