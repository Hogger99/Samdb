import random
from typing import Optional, Dict, Tuple, List, Union, Set
from src.hdc.sdr_types import BIT_TYPE, BIT_WEIGHT_TYPE, BIT_PATTERN_TYPE
from src.hdc.database import select_symbol_encoder, select_symbol_to_bits, insert_symbol_encoder, insert_symbol_to_bits

SYMBOL_TYPE = Union[str, int]
""" the type of symbols that can be encoded """


class SymbolEncoder(object):
    def __init__(self,
                 database: str,
                 name: str,
                 restore: bool = False,
                 dimension: int = 2048,
                 sparsity: float = 0.02,
                 seed: Union[int, str] = 123
                 ):
        """
        class encodes a symbol  into a randomly distributed sparse bit pattern chosen from a population of size dimension
        :param name: name of the encoder
        :param dimension: size of the dimension - this should be large e.g. >= 2048
        :param sparsity: the percentage sparsity that dictates how many bits will be chosen from the dimension. This should be <= 2%
        :param seed: a number or string that sees the randon number generator to ensure we can repeat random experiments
        """

        self._db = database
        """ the database connection string """

        self._name = name
        """ the unique name for the encoder """

        self._id = None
        """ the database id for the encoder """

        if not restore:

            self._dimension = dimension
            """ the size of the dimension from which we will randomly pick bits """

            self._max_nbits: int = max(int(sparsity * dimension), 1)
            """ the maximum number of bits that will be picked from the dimension ensuring a specific sparsity level"""

            # a mapping of symbols to a set of bits
            #
            self._symbols: Dict[SYMBOL_TYPE, Set[BIT_TYPE]] = dict()
            """ map of symbols to the randomly selected bits """

            self._bits: Dict[BIT_TYPE, Set[SYMBOL_TYPE]] = dict()
            """ map of bits to symbols """

        else:
            self.restore()

        random.seed(seed)

    def restore(self) -> Optional[str]:
        """
        restore from the database
        :return: error
        """
        records, error = select_symbol_encoder(db=self._db, where={'encoder_name=': self._name})
        if error is None and len(records) == 1:
            self._id = records[0]['encoder_id']
            self._dimension = records[0]['dimension']
            self._max_nbits = records[0]['max_nbits']

            records, error = select_symbol_to_bits(db=self._db,
                                                   encoder_name=self._name)

            if error is None:
                self._symbols = dict()
                self._bits = dict()
                for record in records:
                    # get the symbol
                    #
                    if record['symbol_int'] is not None:
                        symbol = record['symbol_int']
                        if symbol not in self.symbols:
                            self._symbols[symbol] = set()
                    else:
                        symbol = record['symbol_str']

                    # update _symbols
                    #
                    if symbol not in self._symbols:
                        self._symbols[symbol] = {record['bit']}
                    else:
                        self._symbols[symbol].add(record['bit'])

                    # update _bits
                    #
                    if record['bit'] not in self._bits:
                        self._bits[record['bit']] = {symbol}
                    else:
                        self._bits[record['bit']].add(symbol)
        return error

    def persist(self) -> Optional[str]:
        """
        save the current state to the db
        :return: error
        """
        records, error = select_symbol_encoder(db=self._db, where={'encoder_name=': self._name})
        if error is None:

            persisted_symbol_to_bits = dict()

            # add encoder for first time
            #
            if len(records) == 0:
                record, error = insert_symbol_encoder(db=self._db,
                                                      encoder_name=self._name,
                                                      dimension=self._dimension,
                                                      max_nbits=self._max_nbits)
                if error is None:
                    self._id = record['encoder_id']

            else:
                if len(records) > 0:
                    self._id = records[0]['encoder_id']

                # get persisted symbols and bits
                #
                records, error = select_symbol_to_bits(db=self._db,
                                                       encoder_name=self._name)

                for record in records:
                    if record['symbol_int'] is not None:
                        symbol = record['symbol_int']
                    else:
                        symbol = record['symbol_str']
                    if symbol not in persisted_symbol_to_bits:
                        persisted_symbol_to_bits[symbol] = {record['bit']}
                    else:
                        persisted_symbol_to_bits[symbol].add(record['bit'])


            # now persist missing symbols or bits
            #
            for symbol in self._symbols:
                symbol_str = None
                symbol_int = None

                if isinstance(symbol, str):
                    symbol_str = symbol
                elif isinstance(symbol, int):
                    symbol_int = symbol
                else:
                    error = f"symbol {symbol} not string or int"

                if error is None:
                    if symbol not in persisted_symbol_to_bits:

                        error = insert_symbol_to_bits(db=self._db,
                                                      encoder_id=self._id,
                                                      symbol_int=symbol_int,
                                                      symbol_str=symbol_str,
                                                      bits=list(self._symbols[symbol]))
                    else:
                        missing_bits = set(self._symbols[symbol]) - persisted_symbol_to_bits[symbol]
                        if len(missing_bits) > 0:
                            error = insert_symbol_to_bits(db=self._db,
                                                          encoder_id=self._id,
                                                          bits=list(missing_bits))
                    if error is not None:
                        break

        return error

    def encode(self,
               symbol: SYMBOL_TYPE,
               population: Optional[BIT_PATTERN_TYPE] = None) -> BIT_PATTERN_TYPE:
        """
        encodes a symbol with a randomly distributed bit pattern
        :param symbol: the symbol to encode
        :param population: optional population of bits to select from - the assumption is the population has the correct dimensionality
        :return: a sparse bit pattern with default weights
        """

        # add the symbol if it doesn't already exist
        #
        if symbol not in self._symbols:

            # get the pool of bits to select from
            #
            if population is None:
                pool = range(self._dimension)
            else:
                pool = list(population.keys())

            # randomly select number of bits from population pool and update the symbol to bits mapping
            #
            self._symbols[symbol] = random.sample(pool, k=self._max_nbits)

            # update the bit to symbol mapping
            #
            for bit in self._symbols[symbol]:
                if bit not in self._bits:
                    self._bits[bit] = {symbol}
                else:
                    self._bits[bit].add(symbol)

        # return a dict of bits with default weight of 1.0
        #
        return {bit: 1.0 for bit in self._symbols[symbol]}

    def decode(self, bits: BIT_PATTERN_TYPE) -> List[Tuple[SYMBOL_TYPE, BIT_WEIGHT_TYPE]]:
        """
        decodes a bit pattern back to a symbol
        :param bits: a dictionary where keys represent bits and values represent the bit weight
        :return: a list of symbols sorted in descending order of weight
        """

        # a map to hold the symbol weight
        #
        symbol_map: Dict[SYMBOL_TYPE, BIT_WEIGHT_TYPE] = dict()

        for bit in bits:
            # a bit could be mapped to more than one symbol, although unlikely
            #
            for symbol in self._bits[bit]:
                if symbol not in symbol_map:
                    symbol_map[symbol] = bits[bit]
                else:
                    symbol_map[symbol] += bits[bit]

        # create list of symbols sorted by weight
        #
        symbols = [(symbol, symbol_map[symbol]) for symbol in symbol_map]
        symbols.sort(key=lambda x: x[1], reverse=True)
        return symbols

    def symbols(self) -> List[SYMBOL_TYPE]:
        """
        returns the list of currently encoded symbols
        :return: a list of symbols
        """
        return list(self._symbols.keys())


if __name__ == '__main__':

    host = 'localhost'
    port = 5432
    dbname = 'samdb'
    user = 'samdb_user'
    password = 'samdb123'

    db = f"host={host} port={port} dbname={dbname} user={user} password={password}"


    encoder = SymbolEncoder(database = db,
                            name='test_symbol',
                            restore=False,
                            dimension=2048,
                            sparsity=0.02,
                            seed=123)

    bit_pattern = encoder.encode(symbol='hello')

    error = encoder.persist()

    error = encoder.restore()

    pass
