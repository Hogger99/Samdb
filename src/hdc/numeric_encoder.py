import random
from typing import Optional, Union, Dict, List, Tuple
from src.hdc.sdr_types import BIT_TYPE, BIT_WEIGHT_TYPE, BIT_PATTERN_TYPE

Q_VALUE_TYPE = float
""" the type for a quantised value """

NUMERIC_TYPE = Union[int, float]
""" the type of numeric that can be encoded"""


class NumericEncoder(object):
    def __init__(self,
                 dimension: int = 2048,
                 sparsity: float = 0.02,
                 quantise_step: float = 1,
                 seed: Union[int, str] = 123):
        """
        class encodes (and decodes) numerical values into a randomly distributed sparse bit pattern chosen from a population of size dimension
        :param dimension: size of the dimension - this should be large e.g. >= 2048
        :param sparsity: the percentage sparsity that dictates how many bits will be chosen from the dimension. This should be <= 2%
        :param quantise_step: real numbers will be quantised into distinct buckets / levels dictated by the quantise_step
        :param seed: a number or string that sees the randon number generator to ensure we can repeat random experiments
        """

        self._dimension: int = dimension
        """ the size of the dimension from which we will randomly pick bits """

        self._max_nbits: int = max(int(sparsity * dimension), 1)
        """ the maximum number of bits that will be picked from the dimension ensuring a specific sparsity level"""

        self._q_value: Dict[Q_VALUE_TYPE, List[BIT_TYPE]] = dict()
        """ map of quantised values to the randomly selected bits """

        self._bits: Dict[BIT_TYPE: List[Q_VALUE_TYPE]] = {}
        """ map of bits to quantised values """

        self._q_step: float = quantise_step
        """ the size of a quantisation step / bucket """
        
        self._lower_bit_index: int = 39
        """ the next index to change at the lower end of the quantised range"""

        self._upper_bit_index: int = 0
        """ the next index to change at the upper end of the quantised range"""
        
        self._upper_q_value: Optional[Q_VALUE_TYPE] = None
        """ the current upper quantisation value"""
        
        self._lower_q_value: Optional[Q_VALUE_TYPE] = None
        """ the current lower quantisation value"""

        random.seed(seed)

    def encode(self,
               numeric: NUMERIC_TYPE,
               population: Optional[BIT_PATTERN_TYPE] = None) -> BIT_PATTERN_TYPE:
        """
        encodes a given numeric with a randomly distributed bit pattern, 
        ensuring that the selected bit pattern is similar (has an overlap) to those numerical values that are within _max_nbits * _q_step distance
        :param numeric: the numeric to encode
        :param population: optional population of bits to select from - the assumption is the population has the correct dimensionality
        :return: a sparse bit pattern with default weights
        """
        # quantise the numeric
        #
        q_value = int(numeric / self._q_step) * self._q_step

        # encode FROM: q_value - (q_step * (max_nbits - 1)) TO: q_value + (q_step * (max_nbits - 1))
        # so that we can ensure similar numerical values have an overlap of bits
        #
        q_step_range = (self._q_step * (self._max_nbits - 1))

        # if q_value does not exist then create it
        #
        if q_value + q_step_range not in self._q_value or q_value - q_step_range not in self._q_value:

            # get the population from the standard dimension or from the optional population provided
            #
            if population is None:
                population = set(range(self._dimension))
            else:
                population = set(population.keys())

            # _upper_q_value will be none if no numerics encoded
            #
            if self._upper_q_value is not None:

                if q_value + q_step_range > self._upper_q_value:

                    # we need to create encodings for _upper_q_value up to q_value + (self._q_step * (self._max_nbits - 1))
                    # this ensures values numerically near have similar bits
                    #
                    q_level_bits = self._q_value[self._upper_q_value]
                    curr_q_value = self._upper_q_value + self._q_step

                    while curr_q_value <= q_value + q_step_range:

                        # create a new copy of the previous bits
                        #
                        q_level_bits = q_level_bits.copy()

                        # change the value at the _bit_index to be a randomly selected bit
                        # making sure the randomly selected bit is different from current bit value
                        #
                        q_level_bits[self._upper_bit_index] = random.choice(list(population - set(q_level_bits)))

                        # update the next bit index to be change - wrap around to zero once at end of vector
                        #
                        self._upper_bit_index += 1
                        if self._upper_bit_index >= self._max_nbits:
                            self._upper_bit_index = 0

                        # assign the bits to the q_value
                        #
                        self._q_value[curr_q_value] = q_level_bits

                        # assign the q_value to the bits
                        #
                        for bit in self._q_value[curr_q_value]:
                            if bit not in self._bits:
                                self._bits[bit] = [q_value]
                            else:
                                self._bits[bit].append(q_value)

                        # keep track of the current max of q_value
                        #
                        self._upper_q_value = curr_q_value

                        # now calculate the next q_value to update
                        #
                        curr_q_value += self._q_step

                # check lower range
                #
                if q_value - q_step_range < self._lower_q_value:

                    q_level_bits = self._q_value[self._lower_q_value]
                    curr_q_value = self._lower_q_value - self._q_step
                    while curr_q_value >= q_value - q_step_range:

                        # create a new copy of the previous bits
                        #
                        q_level_bits = q_level_bits.copy()

                        # change the value at the _bit_index to be a randomly selected bit
                        # making sure the randomly selected bit is different from current bit value
                        #
                        q_level_bits[self._lower_bit_index] = random.choice(list(population - set(q_level_bits)))

                        # update the next lower bit index to be change - wrap around to (self._max_nbits - 1) once we get below zero
                        #
                        self._lower_bit_index -= 1
                        if self._lower_bit_index < 0:
                            self._lower_bit_index = self._max_nbits - 1

                        # assign the bits to the q_value
                        #
                        self._q_value[curr_q_value] = q_level_bits

                        # assign the q_value to the bits
                        #
                        for bit in self._q_value[curr_q_value]:
                            if bit not in self._bits:
                                self._bits[bit] = [q_value]
                            else:
                                self._bits[bit].append(q_value)

                        # keep track of the current min of q_value
                        #
                        self._lower_q_value = curr_q_value

                        # now calculate the next q_value to update
                        #
                        curr_q_value -= self._q_step
            else:
                # encode FROM: q_value - (q_step * (max_nbits - 1)) TO: q_value + (q_step * (max_nbits - 1))
                # so that we can ensure similar numerical values have an overlap of bits
                #

                # get the first q_value
                #
                curr_q_value = q_value - q_step_range

                # which must be the min q_value so far
                #
                self._lower_q_value = curr_q_value

                # which will need a random set of bits
                #
                q_level_bits = random.sample(list(population), k=self._max_nbits)

                while curr_q_value <= q_value + q_step_range:

                    # create a new copy of the previous bits
                    #
                    q_level_bits = q_level_bits.copy()

                    # change the value at the _bit_index to be a randomly selected bit
                    # making sure the randomly selected bit is different from current bits
                    #
                    q_level_bits[self._upper_bit_index] = random.choice(list(population - set(q_level_bits)))

                    # update the next upper bit index to be change - wrap around to zero once at end of vector
                    #
                    self._upper_bit_index += 1
                    if self._upper_bit_index >= self._max_nbits:
                        self._upper_bit_index = 0

                    # assign the bits to the q_value
                    #
                    self._q_value[curr_q_value] = q_level_bits

                    # assign the q_value to the bits
                    #
                    for bit in self._q_value[curr_q_value]:
                        if bit not in self._bits:
                            self._bits[bit] = [q_value]
                        else:
                            self._bits[bit].append(q_value)

                    # keep track of the current max of q_value
                    #
                    self._upper_q_value = curr_q_value

                    # now calculate the next q_value to update
                    #
                    curr_q_value += self._q_step

        return {bit: 1.0 for bit in self._q_value[q_value]}

    def decode(self, bits: Dict[BIT_TYPE, BIT_WEIGHT_TYPE]) -> Tuple[Q_VALUE_TYPE, BIT_WEIGHT_TYPE, List[Tuple[Q_VALUE_TYPE,BIT_WEIGHT_TYPE]]]:
        """
        decodes a bit pattern back to a numeric
        :param bits: 
        :return: tuple (most likely numeric, the weight of the numeric, numeric distribution) 
        """
        q_values: Dict[Q_VALUE_TYPE: BIT_WEIGHT_TYPE] = dict()
        max_weight = 0.0
        max_q_value = None

        for bit in bits:
            # a bit could be mapped to more than one q_value due to the similarity encoded
            #
            for q_value in self._bits[bit]:
                if q_value not in q_values:
                    q_values[q_value] = bits[bit]
                else:
                    q_values[q_value] += bits[bit]
                if q_values[q_value] > max_weight:
                    max_q_value = q_value
                    max_weight = q_values[q_value]

        # create the distribution sorted by q_value
        q_value_distribution = [(q_value, q_values[q_value]) for q_value in q_values]
        q_value_distribution.sort(key=lambda x: x[0])

        return max_q_value, max_weight, q_value_distribution

    def quantised_values(self) -> List[Q_VALUE_TYPE]:
        """
        returns the current quantised values that have been encoded 
        :return: a list of encoded quantised values
        """
        return list(self._q_value.keys())
