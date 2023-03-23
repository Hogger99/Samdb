# Testing NumericEncoder

## Introduction

The NumericEncoder is responsible for encoding numbers (ints and floats) as randomly distributed weighted sparse bit patterns in a high dimension.  
We can think of a high dimensional bit pattern as a long list or array of 0s and 1s.  
For efficiency's sake, only the bits with a non-zero value are stored which leads to representing bit patterns as dicts, with the bit number as a key and the bit weight as the value.  
For example a bit pattern with bits 23, 84 and 1002 set with a weight of 1.0 might be represented as:
```python
{23: 1.0, 84: 1.0, 1002: 1.0 ....}
```
The bit pattern is sparse (say 40 bits set out of 2048) because this gives the encoding special mathematical properties:
1. A very large number of numbers (near infinite) can be encoded in a finite dimension even as relatively small as 2048
   1. Unlike other encodings such as Binary - which would need an infinite number of bits to store an infinite number of numerical values 
2. Each randomly selected bit pattern is highly likely to be "orthogonal" (dissimilar) to every other possible pattern
   1. This makes it easier to decode the bit pattern
   2. However, this property means that special care is needed to ensure numbers "close" to each other on the number line have similar bit patterns
3. The encoding is robust to noise
   1. Even with 50% of the bits missing we are highly likely to decode the bit pattern accurately
   2. Other encodings such as Binary are not robust as the corruption of 1 bit changes the semantic meaning of the data
4. Calculating the similarity between two patterns is as simple as calculating the overlap of bits in the two patterns

A key feature of the NumericEncoder is that numbers that are close to each other, (on the real number line), have similar bit patterns.  
This takes special care thanks to property 2 above. 

The NumericEncoder requires the size of the high dimension, the required sparsity, the quantise_step to convert an infinitely long REAL number to a quantised level and a random generator seed that ensures experiments can be repeated
```python
class NumericEncoder(object):
    def __init__(self,
                 dimension: int = 2048,
                 sparsity: float = 0.02,
                 quantise_step: float = 1,
                 seed: Union[int, str] = 123):
```
The sparsity is used to calculate the number of bits that will be randomly selected from the population defined by dimension for each new number.  
To deal with floating numbers, the NumericEncoder first rounds the number to the nearest quantise_step.  
To ensure numbers close to each other have similar bit random patterns, the encoder must base the random patterns on previously seen numbers that are close.  
The first number to be encoded is has a simply randomly picked nit pattern. Then for the numbers close that are close to the first number, the bit patterns are  
based on the previous bit pattern, with a single bit randomly changed.  This leads to a single bit being different between two numbers that are a single quantise_step away.
For example: let's say that the value 100 has the bit pattern:
```python
{23: 1.0, 84: 1.0, 74: 1.0, 1002: 1.0, .....}
```
If the quantise_step is set to 1.0 then the number 101 would have the bit pattern with a single bit different:
```python
{48: 1.0, 84: 1.0, 74: 1.0, 1002: 1.0, .....}
```
