from typing import Optional, Dict, Union
from copy import deepcopy
from src.hdc.sdr_types import BIT_PATTERN_TYPE
from symbol_encoder import SymbolEncoder
from numeric_encoder import NumericEncoder

SDR_VALUE_TYPE = Dict[str, Union[str, int, float, list, dict]]


class ESDR(object):
    def __init__(self,
                 esdr: Optional = None):
        """
        Class represents a generalised memory of a data concept as a randomly distributed weighted sparse high dimensional bit pattern.
        A HIGH DIMENSIONAL bit pattern has a large number of bits, e.g. >= 2048 bits. A SPARSE bit pattern has only a small number of bits with
        non-zero value. A WEIGHTED bit pattern has bits with REAL values i.e. between 0.0 and 1.0
        A key requirement is that similar data concepts will contain a proportion of the same bits in their pattern whereas dissimilar
        concepts will share none or a very small proportion of bits.
        Key features of this class are:
        - it provides a method to calculate the similarity between two generalised memories - this is a relatively straight forward simple
            mathematical process of calculating the overlap of bit values present in each pattern.
        - it provides a method to combine (bundle) simple different data concepts together to form complex concepts
        - it provides a method to "learn" the generalised features of the data concepts that make up the memory
         :param esdr: optional ESDR from which to make a copy from
        """
        self._bits: BIT_PATTERN_TYPE = dict()
        """ map of bits to weights """

        if isinstance(esdr, ESDR):
            self._bits = deepcopy(esdr.bits())
        else:
            if isinstance(esdr, (set, list)):
                self._bits = {bit: 1.0 for bit in esdr}

        # the sum of weights should always equal the number of initial bits set
        #
        self._sum_bits = sum([self._bits[bit] for bit in self._bits])
        """ the sum of all weights in the pattern """

    def bits(self) -> BIT_PATTERN_TYPE:
        """
        the current bit pattern
        :return: the bit pattern structure
        """
        return self._bits

    def __copy__(self):
        return ESDR(esdr=self)

    def overlap(self, esdr) -> float:
        """
        method to calculate the weighted overlap of bits with another ESDR
        :param esdr: the ESDR to compare to
        :return: the total weight of overlap
        """

        # get a reference to the ESDR bits
        #
        esdr_bits = esdr.bits()

        # the sum of the minimum values of overlapping bits
        #
        return sum([min(self._bits[bit], esdr_bits[bit]) for bit in set(self._bits.keys()) & set(esdr_bits.keys())])

    def similarity(self, esdr) -> float:
        """
        method to calculate the similarity to another ESDR
        :param esdr: the ESDR to compare to
        :return:
        """
        if self._sum_bits > 0.0:
            return self.overlap(esdr=esdr) / self._sum_bits
        else:
            return 0.0

    def learn(self, esdr, learn_rate: float = 0.7) -> None:
        """
        method to learn the features of an ESDR
        :param esdr: the ESDR to learn from
        :param learn_rate: the rat eof learning - if 0.0 then no learning, if 1.0 then ESDR is effectively copied.
                To generalise then the learn_rate must be < 1.0
        :return: None
        """

        # get a reference to the ESDR bits
        #
        esdr_bits = esdr.bits()

        # the learn rate is used to stregthen the common bit weights and the inv_rate is used to weaken the uncommon bits
        #
        inv_rate = 1 - learn_rate

        # get a set of all the bits present in both
        #
        all_bits = set(self._bits.keys()) | set(esdr_bits.keys())

        self._sum_bits = 0.0
        for bit in all_bits:

            # if the bit is in both
            #
            if bit in esdr_bits and bit in self._bits:
                self._bits[bit] = (self._bits[bit] * inv_rate) + (learn_rate * esdr_bits[bit])

            # else if only in self
            #
            elif bit not in esdr_bits:
                self._bits[bit] = (self._bits[bit] * inv_rate)

            # else must be in sdr_bits
            else:
                self._bits[bit] = (learn_rate * esdr_bits[bit])

            # keep track of the sum of all weights
            #
            self._sum_bits += self._bits[bit]

    def bundle(self, sdr, bit_label: str = None) -> None:
        sdr_bits = sdr.bits()
        if bit_label is not None:
            for bit in sdr_bits:
                self._bits[(bit_label, bit)] = sdr_bits[bit]
        else:
            for bit in sdr_bits:
                self._bits[bit] = sdr_bits[bit]

    def set_value(self,
                  data_concept: SDR_VALUE_TYPE,
                  field_encoder: SymbolEncoder,
                  symbol_encoder: SymbolEncoder,
                  numeric_encoder: NumericEncoder) -> Dict[str, str]:

        fields = {}
        if isinstance(data_concept, dict):
            for field in data_concept:
                if isinstance(data_concept[field], (str, int, float)):
                    field_bit_pattern = field_encoder.encode(symbol=field)
                    if isinstance(data_concept[field], str):
                        value_bit_pattern = symbol_encoder.encode(symbol=data_concept[field], population=field_bit_pattern)
                        fields[field] = 'symbol'
                    else:
                        value_bit_pattern = numeric_encoder.encode(numeric=data_concept[field], population=field_bit_pattern)
                        fields[field] = 'numeric'

                    for bit in value_bit_pattern:
                        self._bits[bit] = value_bit_pattern[bit]
                elif isinstance(data_concept[field], list):
                    for item_idx in range(len(data_concept[field])):
                        field_bit_pattern = field_encoder.encode(symbol=f"{field}_{item_idx}")
                        if isinstance(data_concept[field][item_idx], str):
                            value_bit_pattern = symbol_encoder.encode(symbol=data_concept[field][item_idx], population=field_bit_pattern)
                            fields[field] = 'symbol'
                        else:
                            value_bit_pattern = numeric_encoder.encode(numeric=data_concept[field][item_idx], population=field_bit_pattern)
                            fields[field] = 'numeric'

                        for bit in value_bit_pattern:
                            self._bits[bit] = value_bit_pattern[bit]

        return fields



