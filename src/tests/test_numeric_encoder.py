import src.hdc.numeric_encoder as enc
import pytest

"""
test spec for the Symbol Encoder
"""


@pytest.fixture
def get_encoder():
    """
    fixture to create a SymbolEncoder
    :return:
    """
    return enc.NumericEncoder(dimension=2048,
                              sparsity=0.02,
                              quantise_step=1.0,
                              seed=123)


@pytest.fixture
def get_test_encodings(get_encoder):
    return {'100': get_encoder.encode(numeric=100),
            '100_2': get_encoder.encode(numeric=100),
            '80': get_encoder.encode(numeric=80),
            '120': get_encoder.encode(numeric=120),
            '140': get_encoder.encode(numeric=140),
            '60': get_encoder.encode(numeric=60),
            }


def test_encode_sparsity(get_test_encodings):
    assert len(get_test_encodings['100'].keys()) == 40


def test_encode_bit_population(get_test_encodings):
    bits = [bit for bit in get_test_encodings['100'].keys()]
    assert min(bits) >= 0 and max(bits) < 2048


def test_encode_consistency(get_test_encodings):
    bits_1 = set(get_test_encodings['100'].keys())
    bits_2 = set(get_test_encodings['100_2'].keys())

    # expect every bit to overlap
    assert len(bits_1 & bits_2) == 40


def test_encode_similarity(get_test_encodings):
    bits_100 = set(get_test_encodings['100'].keys())
    bits_80 = set(get_test_encodings['80'].keys())
    bits_120 = set(get_test_encodings['120'].keys())

    # expect 1 bit to overlap
    assert len(bits_100 & bits_80) == 20 and len(bits_100 & bits_120) == 20


def test_encode_dissimilarity(get_test_encodings):
    bits_100 = set(get_test_encodings['100'].keys())
    bits_140 = set(get_test_encodings['140'].keys())
    bits_60 = set(get_test_encodings['60'].keys())

    # expect close to zero bits overlap
    assert len(bits_100 & bits_140) <= 2 and len(bits_100 & bits_60) <= 2


def test_decode(get_test_encodings, get_encoder):

    decoded_numeric = get_encoder.decode(bits=get_test_encodings['100'])

    # expect a list of tuples containing (max_probable_numeric, weight, distribution)
    assert len(decoded_numeric) == 3 and decoded_numeric[0] == 100
