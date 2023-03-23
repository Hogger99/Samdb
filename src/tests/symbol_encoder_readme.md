# Testing SymbolEncoder

## Introduction

The SymbolEncoder is responsible for encoding symbols (strings or ints) as randomly distributed weighted sparse bit patterns in a high dimension.  
We can think of a high dimensional bit pattern as a long list or array of 0s and 1s. For efficiency's sake, only the bits with a non-zero value are stored which leads to representing bit patterns as dicts, with the bit number as a key and the bit weight as the value.  
For example a bit pattern with bits 23, 84 and 1002 set with a weight of 1.0 might be represented as:
```python
{23: 1.0, 84: 1.0, 1002: 1.0 ....}
```
The bit pattern is sparse (say 40 bits set out of 2048) because this gives the encoding special mathematical properties:
1. A very large number of symbols (near infinite) can be encoded in a finite dimension even as small as 2048
   1. Unlike other encodings such as Binary - which would need an infinite number of bits to store an infinite number of symbolic values 
2. Each randomly selected bit pattern is highly likely to be "orthogonal" (dissimilar) to every other possible pattern
   1. This makes it easier to decode the bit pattern
3. The encoding is robust to noise
   1. Even with 50% of the bits missing we are highly likely to decode the bit pattern accurately
   2. Other encodings such as Binary are not robust as the corruption of 1 bit changes the semantic meaning of the data
4. Calculating the similarity between two patterns is as simple as calculating the overlap of bits in the two patterns

This version of the SymbolEncoder makes use of property No 2 above to ensure every symbol has a dissimilar bit pattern from any other symbol.

The SymbolEncoder requires the size of the high dimension, the required sparsity and a random generator seed that ensures experiments can be repeated
```python
class SymbolEncoder(object):
    def __init__(self,
                 dimension: int = 2048,
                 sparsity: float = 0.02,
                 seed: Union[int, str] = 123):
```
The sparsity is used to calculate the number of bits that will be randomly selected from the population defined by dimension for each new symbol

In order to facilitate decoding previously encoded symbols SymbolEncoder maintains maps between each symbol and their associated bits
```python
# a mapping of symbols to a set of bits
#
self._symbols: Dict[SYMBOL_TYPE, Set[BIT_TYPE]] = dict()
""" map of symbols to the randomly selected bits """

self._bits: Dict[BIT_TYPE, Set[SYMBOL_TYPE]] = dict()
""" map of bits to symbols """
```

## Tests

The tests will need to share an instance of a SymbolDecoder achieved by declaring a fixture:
```python

@pytest.fixture
def get_encoder():
    """
    fixture to create a SymbolEncoder
    :return:
    """
    return enc.SymbolEncoder(dimension=2048,
                             sparsity=0.02,
                             seed=123)
```

In addition, we will need some test bit patterns:

```python
@pytest.fixture
def get_test_encodings(get_encoder):
    return {'hello': get_encoder.encode(symbol='hello'),
            'hello_2': get_encoder.encode(symbol='hello'),
            'goodbye': get_encoder.encode(symbol='goodbye'),
            'terminator': get_encoder.encode(symbol='Ill be back')
            }
```

### Test 1 Checking sparsity

Given that the encoder is initialised with sparsity of 2% (i.e. 0.02) we would expect the number of bits to be set to be
> 2048 * 0.02 = 40

As the bit pattern only stores bits with a weight greater than zero this is simply checked by counting the number of bits
```python
def test_encode_sparsity(get_test_encodings):
    assert len(get_test_encodings['hello'].keys()) == 40
```

### Test 2 Checking the bit values
Given that the encoder is initialised with a dimension of 2048 we would expect the bits selected to be:
>  2048 < bit >= 0

```python
def test_encode_bit_population(get_test_encodings):
    bits = [bit for bit in get_test_encodings['hello'].keys()]
    assert min(bits) >= 0 and max(bits) < 2048
```

### Test 3 Check consistent encodings of the same symbol

The encoding of a symbol should always be the same. This is verified by making two calls to the encoder with the same string and checking that the exact same bits are returned.

```python 
def test_encode_consistency(get_test_encodings):
    bits_1 = set(get_test_encodings['hello'].keys())
    bits_2 = set(get_test_encodings['hello_2'].keys())

    # expect every bit to overlap
    assert len(bits_1 & bits_2) == 40
```

### Test 4 Check an encoded symbol is correctly decoded

The decoder should return a list of probable symbols for a given encoding
```python
def test_decode(get_test_encodings, get_encoder):

    decoded_symbol = get_encoder.decode(bits=get_test_encodings['hello'])

    # expect a list of tuples containing (symbol, weight)
    assert len(decoded_symbol) > 0
    assert decoded_symbol[0][0] == 'hello'

```

### Test 5 Check that a corrupted bit pattern can still be decoded

Two create a corrupted bit pattern we merge bits from two encodings and test if the most represented symbol is decoded

```python
def test_decode_noisy_bit_pattern(get_test_encodings, get_encoder):
    
    hello_bits = list(get_test_encodings['hello'].keys())
    goodbye_bits = list(get_test_encodings['goodbye'].keys())

    # take first 30 bits from hello
    noisy_bit_pattern = {bit: 1.0 for bit in hello_bits[:30]}

    # add in first 10 bits from goodbye
    noisy_bit_pattern.update({bit: 1.0 for bit in goodbye_bits[:10]})

    # decode
    decoded_symbol = get_encoder.decode(bits=noisy_bit_pattern)

    # expect at least two symbols
    assert len(decoded_symbol) >= 2

    # expect hello to be most probable
    assert decoded_symbol[0][0] == 'hello'

    # expect goodbye to be second most probable
    assert decoded_symbol[1][0] == 'goodbye'
```

### Test 6 Check that the encodings are generated randomly

If the encodings are generated randomly then the probability of an overlap of bits across several encodings is close to zero

```python
def test_random_bit_pattern(get_test_encodings):

    hello_bits = set(get_test_encodings['hello'].keys())
    goodbye_bits = set(get_test_encodings['goodbye'].keys())
    terminator_bits = set(get_test_encodings['terminator'].keys())

    overlap = len(hello_bits & goodbye_bits & terminator_bits)

    # expect overlap to be 2 or less
    assert overlap <= 2

```
