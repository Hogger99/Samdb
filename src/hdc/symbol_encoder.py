import random
from typing import Optional, Dict, Tuple, List, Union, Set
from src.hdc.sdr_types import BIT_TYPE, BIT_WEIGHT_TYPE, BIT_PATTERN_TYPE

SYMBOL_TYPE = Union[str, int]
""" the type of symbols that can be encoded """


class SymbolEncoder(object):
    def __init__(self,
                 dimension: int = 2048,
                 sparsity: float = 0.02,
                 seed: Union[int, str] = 123):
        """
        class encodes a symbol  into a randomly distributed sparse bit pattern chosen from a population of size dimension
        :param dimension: size of the dimension - this should be large e.g. >= 2048
        :param sparsity: the percentage sparsity that dictates how many bits will be chosen from the dimension. This should be <= 2%
        :param seed: a number or string that sees the randon number generator to ensure we can repeat random experiments
        """

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

        random.seed(seed)

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
