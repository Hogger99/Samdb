import src.hdc.symbol_encoder as enc
import pytest

"""
test spec for the Symbol Encoder.
"""

@pytest.fixture
def get_encoder():
    """
    fixture to create a SymbolEncoder
    :return:
    """
    return enc.SymbolEncoder(dimension=2048,
                             sparsity=0.02,
                             seed=123)


@pytest.fixture
def get_test_encodings(get_encoder):
    return {'hello': get_encoder.encode(symbol='hello'),
            'hello_2': get_encoder.encode(symbol='hello'),
            'goodbye': get_encoder.encode(symbol='goodbye'),
            'terminator': get_encoder.encode(symbol='Ill be back')
            }


def test_encode_sparsity(get_test_encodings):
    assert len(get_test_encodings['hello'].keys()) == 40


def test_encode_bit_population(get_test_encodings):
    bits = [bit for bit in get_test_encodings['hello'].keys()]
    assert min(bits) >= 0 and max(bits) < 2048


def test_encode_consistency(get_test_encodings):
    bits_1 = set(get_test_encodings['hello'].keys())
    bits_2 = set(get_test_encodings['hello_2'].keys())

    # expect every bit to overlap
    assert len(bits_1 & bits_2) == 40


def test_decode(get_test_encodings, get_encoder):

    decoded_symbol = get_encoder.decode(bits=get_test_encodings['hello'])

    # expect a list of tuples containing (symbol, weight)
    assert len(decoded_symbol) == 2
    assert decoded_symbol[0][0] == 'hello'


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


def test_random_bit_pattern(get_test_encodings):

    hello_bits = set(get_test_encodings['hello'].keys())
    goodbye_bits = set(get_test_encodings['goodbye'].keys())
    terminator_bits = set(get_test_encodings['terminator'].keys())

    overlap = len(hello_bits & goodbye_bits & terminator_bits)

    # expect overlap to be 2 or less
    assert overlap <= 2
