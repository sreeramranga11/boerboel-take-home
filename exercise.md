An Online Trimmed Average Calculator.
=====================================

#### Summary

Your task is to develop a Python program that can perform an online, moving, trimmed
average calculation.  The program will also handle decoding of an input stream following a
binary encoding scheme based on base64.  The decoded input is a custom, variable-length
instruction set with instructions for setting various calculation parameters and providing
sample data from which to compute the trimmed average.

#### Background

In statistics, a trimmed estimator is derived from another, underlying estimator.  The
result of a trimmed estimator is calculated using the underlying estimator, but after
discarding extreme values at the high and low ends of a sample distribution.  For example,
the trimmed average of a sample set is the mean of all samples in the set after discarding
some number of the highest and/or lowest samples.

A moving, or "rolling", estimator is the result of applying a statistical estimator on
multiple subsets of a sequence of samples.  The subsets constitute a (typically fixed)
window that can be thought of as "sliding" over the sample sequence, with each position of
the window corresponding to a different subset and yielding a distinct resulting value.
For example, a moving average with a window size of 10 applied to a sequence of 20 samples
would yield a new sequence with 11 values.  The first value in this new sequence would be
the average of the first 10 samples, the second value would be the average of the samples
between the 2nd and 11th (inclusively), the third would be the average of the samples
between the 3rd and 12th, and so on to the 11th and final value, which would be the
average of the samples between the 11th and 20th samples.

An online calculation is one that can perform its function "piece-by-piece".  In contrast
with an "offline" calculation, which must process all of its input in order to produce any
output, an online calculation immediately produces partial output as soon as it has
processed enough input in order to do so.  For example, an online version of the above
moving average calculation would produce the first value in the resulting sequence as soon
as it has finished processing the 10th input sample.  Then it would produce a new moving
average value on every subsequent input processed.  Online calculations are important for
streaming use-cases where the entirety of its input may not fit in main memory, or for
cases where fast delivery of partial results are required.

#### Specification

##### Trimming Policy

The specification for how extreme values are trimmed are given independently for both high
values and low values.  For each extreme, up to two parameters may be specified for
trimming: the absolute number of samples (`n_abs`), and the number of samples expressed as
a proportion of the window size (`n_prop`).  For a given `n_abs`, the `n_abs` most extreme
values must be excluded from the computed average.  A value of `0` indicates that no
exclusions are to be made.  For a given `n_prop`, the `m` most extreme values must be
excluded from the computed average, where `m = ceil(n_prop * window_size / 100)`.  A
value of `0` indicates that no exclusions are to be made.  Where values for both `n_abs`
and `n_prop` are given, the specification that calls for more trimming is to be used.  For
example, for `n_abs = 3` and `n_prop = 10` the three most extreme values are to be
excluded for small window sizes.  For increasing window sizes starting at 21 the
proportional specification is equally "trim-happy" (`ceil(10 * 21 / 100) = 3`), and
becomes dominant for window sizes greater than or equal to 31 (`ceil(10 * 31 / 100) =
4`).

  Notes:
   - Recall that these parameters are given independently for both high and low values,
     and so up to four total parameters may be given to specify trimming criteria covering
     both extremes.

   - The average of a set of samples is not defined when the set is empty, and the same is
     true for trimmed averages where all the samples in a set have been excluded due to
     trimming.

##### Encoded Input

The "raw" input to the program is a binary stream, the format of which is detailed below.
The input, as presented through the program's standard input stream, is an ASCII-formatted
text stream.  This "encoded" input consists of a non-zero number of lines.  The lines are
all delimited with a "newline" (`\n`) character.  Lines may start with a `#` character.
These lines are optional comments and are to be discarded without any further processing.
Other lines may start and/or end with extraneous whitespace (`' ', '\t', '\n'`).  Such
whitespace should be removed from the line prior to processing.  Any lines that are empty
or only consist of whitespace are to be discarded.  The text content remaining in all
other lines are base64-encoded binary strings with any trailing `=` characters removed
from the encoding.  The raw input to the program is reconstructed by appending the correct
number of `=` characters and then base64-decoding each successive encoded string in the
input and concatenating the binary results in series.

  Notes:
   - In general, the above encoding is not unique for a given binary stream.  The raw
     input sequence can be broken up into any number of pieces and at any points within
     the sequence.  The only guarantee is that the original stream can be reconstructed
     without loss from the given encoded lines.

##### Raw Input

The raw input is a stream of binary data segments.  Each segment starts with a code that
is a 1-byte unsigned integer.  The code can take on one of a number of pre-defined values.
Depending on the value of the code, it may be followed by an additional argument, which
may be a 1- or 4-byte unsigned integer.  The code may also be followed by additional data.
After any such data the end of the segment is reached and may be followed by a new segment
with its own code and optional data.  This sequence of segments continues until the end of
the stream.  The code values, their meaning, and any optional arguments are detailed in
the table below.  All packed multi-byte sequences are given in big-endian order.  The
program must maintain an internal state that tracks the window size, trimming options, and
any observed samples.  Initially, this state has no window size set, nor any trimming
options set, and has not observed any samples.  This state is updated in response to the
given segment according to the details noted below:

| code      | mnemonic      | arg size |
| --------- | ------------- | -------- |
| 0x00      | `RESET`       |        0 |
| 0x01      | `SLAT`        |        1 |
| 0x02      | `SUAT`        |        1 |
| 0x03      | `SLPT`        |        1 |
| 0x04      | `SUPT`        |        1 |
| 0x05      | `SWS`         |        4 |
| 0x10      | `NEW_SAMPLES` |        1 |

 - RESET: "Clear" the internal averaging window.  Maintains the window size and any
   trimming values set.  The averaging window is now "empty" and needs to be refilled with
   new processed samples before producing more trimmed averages.

 - SLAT ("Set Lower Absolute Trim"): Set `n_abs` for low values.  Also implies RESET if
   the original value differs from that provided.

 - SUAT ("Set Upper Absolute Trim"): Set `n_abs` for high values.  Also implies RESET if
   the original value differs from that provided.

 - SLPT ("Set Lower Proportional Trim"): Set `n_prop` for low values.  Also implies RESET
   if the original value differs from that provided.

 - SUPT ("Set Upper Proportional Trim"): Set `n_prop` for high values.  Also implies RESET
   if the original value differs from that provided.

 - SWS ("Set Window Size"): Set the window size.  The argument is a 4-byte unsigned
   integer value to use for the new window size (`<=100,000`).  Also implies RESET if the
   original window size differs from that provided.

 - NEW_SAMPLES: Provide one or more samples.  The argument is the number of samples that
   follow.  Immediately following the argument is that many samples, each an 8-byte
   double-precision floating point number.

##### Output

Your program must calculate a trimmed average for every eligible sample window.  For
example, given a window size of 3, your program must calculate a trimmed average of the
first three samples following the instruction setting the window size, another trimmed
average after processing the 4th sample (of samples 2, 3, and 4), another after processing
the 5th sample (of samples 3, 4, and 5), and so on for as many samples as are given.  If a
`RESET` instruction is specified (or another instruction given that implies a `RESET`),
then your program must thereafter go on to collect an entirely new set of three samples
(or `window_size` samples if the window size has changed) after which point it would
calculate a new trimmed average for those samples.  Then, it would continue to calculate
trimmed averages on a rolling bases as before for as many samples as are given, or upon
processing the next `RESET`.

Your program must output a sequence of lines, one for each trimmed average that it
calculates.  Each line must follow the format `{index}: {t_avg}` where `index` is the
number of samples processed since the last `RESET` (either in response to an explicit
`RESET` segment or to another segment implying a `RESET`), or since the beginning of
program execution if no such `RESET` occurred; and `t_avg` is the computed trimmed average
using the most up-to-date sample window and trim settings.  The `index` must be
right-aligned and padded with spaces so that it takes up at least 7 characters.  The
`t_avg` must be formatted as a plain floating-point number (e.g.: no scientific notation)
and rounded to the nearest thousandths place (three places to the right of the decimal
point).  If the trimmed average is not defined, either due to a lack of samples or no
window size specified, then output the string "NaN" in place of `t_avg`.

#### Examples

The examples below show three views of the sample input: the encoded form as it would be
presented to the program, the decoded, raw binary form that the program will need to
reconstruct, and a "disassembly" of the raw binary form illustrating the encoded
instructions.  Multiple lines of the encoded input are spread and shown over multiple
columns for compactness.

##### Example 1

Encoded Input:

```
# These lines   mZk          AA
# should be     mZo/         AD8
# ignored       0zMz         4zMzMw
AQECAQUAAA      MzM          MzMz
AAU             MzM          Pw
AwIEFhA         P9k          5mZm
CD+5mZmZmQ      mQ           ZmY
mZo             mZmZmZo/     ZmY
Pw              4AAA         Pw
yZmZ            AAA          6ZmZmZmZmg
```

Decoded Input:

```
00000000: 0101 0201 0500 0000 0503 0204 1610 083f  ...............?
00000010: b999 9999 9999 9a3f c999 9999 9999 9a3f  .......?.......?
00000020: d333 3333 3333 333f d999 9999 9999 9a3f  .333333?.......?
00000030: e000 0000 0000 003f e333 3333 3333 333f  .......?.333333?
00000040: e666 6666 6666 663f e999 9999 9999 9a    .ffffff?.......
```

Disassembled Input:

```
SLAT  1
SUAT  1
SWS   5
SLPT  2
SUPT 22
NEW_SAMPLES 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8
```

Example Output:

```
      5: 0.250
      6: 0.350
      7: 0.450
      8: 0.550
```

##### Example 2

Note how the encoding differs from the first example, but otherwise encodes for exactly
the same binary input stream.  Thus, the exact same output is expected.

Encoded Input:

```
AQEC            mQ           AAA
AQU             mQ           AAA
AA              mj/JmQ       AD8
AAA             mZmZmZo      4zMzMzMzMw
BQ              Pw           Pw
AwI             0w           5g
BA              MzM          ZmY
Fg              Mw           Zg
EAg             Mw           ZmZm
Pw              Mw           Pw
uQ              Mz/ZmQ       6ZmZmQ
mQ              mQ           mZk
mQ              mQ           mg
mQ              mZmaP+AA
```

Decoded Input:

```
00000000: 0101 0201 0500 0000 0503 0204 1610 083f  ...............?
00000010: b999 9999 9999 9a3f c999 9999 9999 9a3f  .......?.......?
00000020: d333 3333 3333 333f d999 9999 9999 9a3f  .333333?.......?
00000030: e000 0000 0000 003f e333 3333 3333 333f  .......?.333333?
00000040: e666 6666 6666 663f e999 9999 9999 9a    .ffffff?.......
```

Disassembled Input:

```
SLAT  1
SUAT  1
SWS   5
SLPT  2
SUPT 22
NEW_SAMPLES 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8
```

Example Output:

```
      5: 0.250
      6: 0.350
      7: 0.450
      8: 0.550
```

##### Example 3

Note how the trimmed averages "start over" after the program encounters an instruction
increasing the window size from 5 to 128 (implying a `RESET`), but _not_ after the third
`SWS` instruction.  This is because the instruction in question designates a window size
of 128, but the window size is _already_ 128 by the time this instruction is encountered.

Encoded Input:

```
AQECAQU                                      Jj/hSVWW
AA                                           cm8S
AAAFAwIEFhA                                  P90
CD+5mZmZmZk                                  O+M
mg                                           WUAuuD/W3BelboKwv+E
P8mZmZmZmZo/0zMzMzM                          AO9vSAGQvw
MzM/2ZmZmZmZmj/gAAAAAAAAP+MzMzMzMzM/5g       5ml81tM
ZmZmZmZm                                     aOo/6XxO
P+mZmZmZmZoFAAAAgA                           5c46Nr/l+Q
EA                                           stzL31q/
Cr/PvH+4lg                                   yNLx6hbYcL/lPA
p+g                                          fQ
P9M                                          T4oxlr/d
FAs                                          3P0q70sMvw
zxY                                          3ISHqPgmdD/vIhDU
NsC/4g                                       4S0
pw                                           oL/kHEIC
fbOHLoQ                                      j6kkv9Qq5Ua3lww
v+PxIobk4mg/0V4                              v+xl
sPEs                                         Bg
O6A/s8w                                      dg
dW5W                                         aAMi
oA                                           P+Ld6MLC
QA                                           VEw/ug
vw                                           +6w
7tI                                          WF0
ZlaXw8i/6OEnfIVXLA                           Xw
v+k                                          8L/sc3U
6jP75FcWP+O60G/ng6IFAAAAgBD1Pw               c8TS
sATk4Q                                       BL/oC3iuLHe+P98W
2gvgvw                                       GXxpO8Q/7sKtKdM8Gj/EAZHWUz2Avw
320bjR9n1D/miag                              4ByWv8Gq
0Xeu4r/TAROvC4P4P8ompl2Gweg/1YRJofkz3A       TD/sX7cW8Rjov+Qw4kU
v7g6KqgoVg                                   +j9K
EL/hSEcJIqc                                  P9IQfp1GBBi/vqLQ3chQgL/k8ryEXj4
7A                                           Fj/kgeA/h0U
P+K6YDgexra/72y6iZHsiA                       mr+AB2hLJb4AP+Y
P+u5BbaPRU6/                                 iooNYYQ
0PAxX65D9A                                   YA
v+vh                                         v8o
37IKc7Y                                      0g
v+5OM68                                      OJq//Q
C2CWPw                                       aL8
2g                                           4Q
GpIfRrw                                      Cu8
ZL+U                                         4xAh4L/B/g
2IPyPfkAv5l60xkTEoA                          4dtz1Ki/1R8
P9rpII4                                      xg
0P0                                          AKw
eA                                           suA
v9GRl/Zz7wy/0CU                              v+lIUNmWJSy/4Boh5EnV2j/a
DErDy+Q                                      /p9p0iRc
v+E                                          v8g
QFeXfLE                                      Vc9izk7Iv+1HGfrntj6/4yV54yo
hL/c                                         DA
2PEug5ywv9RRN81goai/4o1cNQ                   zL8
t84cP6V3                                     6TiKBU21lr/gMPrS/k0
5dg                                          GD8
Hw                                           1PEQOw
gaA/                                         p/OkP+Iy0iocx2y/5MZ96g
2JeI//lLbD++ELGBrYXgP9bRcz+DiBg/698dlOE+     odeiP+Q
tj/tboJOx+F8P+w                              VUJw
XsetiQ                                       elcSv7wilHt1AA
1xY/                                         oD/jfH8ErcvI
18FqD36y/D/pARHamt8                          Pw
ND+6zhqhjdzQP+PB                             uQ
jb47                                         LJoduNEQP+C4hmENvAC/5Smu
LpI/hVNJ                                     JzdWUD/C
4nY                                          a+UHaEAIP+TbEJI
HoC/7gU                                      pD9mv+9nzQ
TM6BNQ                                       xIIB3L/u7itDSm4CP+Zb
4D8                                          RA
5L6W                                         tw
Y39yAD/r+wuRySvG                             qKHaPw
P+M1TQ                                       7CX2J6ZA
gJObOL/Gmw                                   kL/h1jTP3YskP8g
sWVMfGi/5Q                                   txYeFiyAv9Wpowc9axA/3ODIVKQuYD/BcXQ
z8U                                          6vWKaD/YeMdsNE0cPw
TeSWRr/HKbFF6k/gP+z905LH                     5M2I0yJEjj+2/g
nFq/69kU                                     K33/hFC/3nDISk2LlA
m8ObaL/MFE0kpGtw                             P+R+aC2D+5S/
v8hnHPNUmLg                                  5sUNQg
vw                                           jKDev8ICT/LT0TA/3HNhFb6BDD/mc4zOh6c0v9vphcnckgA/71s0Rg
2WE868k                                      TuLEv8c4
nFy/6Ls                                      pSsc
4V4c                                         VyC/2/w
oQ                                           4kL5
0r/fWuO63KogP9w                              I/C/
2gX0qSE4                                     1g
v+G3vlc9z9y/                                 Aw2ZcjxYP35W1y3MUAC/1A
6g                                           dhFXuwPEP+9y
fDCX                                         vmjELeq/72qL74OLkj/ePg
7Q                                           rTp80cC/
TSQ                                          1w
P90                                          J3uDbBkwv+JDew
7KTKuT/gP8+Q                                 jIHrAL/m0pnPqwbiv+Hw
eTxWOg                                       Fbc
2D/cQ3w5                                     v06kP95H/+TlHii/3nRuo88vzL8
U7WM                                         4Q
vw                                           4wcxtam2v624dvdf
7g                                           h2C/pt6lNrnjgL/LYHQ
pOSxnnLsv9qj                                 Phce+L8
NGC4                                         2EI
Igi/                                         GCZquA
2A                                           7A
vtD4Zss                                      P9Q
IL+X0Zuwk1AAP71D6r8                          w/RN
NuBQ                                         UaewP+x5/g
P9E                                          +Q
jA                                           jiNwvw
tTAV                                         4ek
W9A/                                         uRUI7Gy/2N2uEhz8
4Iqt                                         VD8
i8ccJD/NAKOL7j4w                             0L4H/g
v7Ijuqpr3sC/635DjshfSr/chIPVeQ               VMOQPw
VRA/6MpgSg                                   r0KZeQKrwL/l
/Q                                           BgprV6zcP9g
43w/5L0                                      QKY3
G7g                                          Ve9c
8VPqP9VUrdsEYEg/5zTH5Qr8                     v+3qu/s
UD/FObbQOpF4v+ZzMFmCgx4                      R0MIvw
P9I                                          0E3HWA
I/4izGY                                      pPuc
SL8                                          P+YQTruxZGi/
7w                                           67MMpe8
uEpYNGoqPw                                   l86/
5k0U9A                                       5mq/DAVmcj/ZRg
iMs                                          aNQvEdA/uL0j9RKU
dD/cccu9                                     wD8
lBrAv+GpCw                                   1w
1CX4Nj/p1Mg                                  zYPZ3V0kP9JI
CdJt6L/k                                     Zwc6n3i/0Aw32w/s0D/e
GJo                                          jic3
qPoudr8                                      31iMP9hbAXCAq3S/05k
5WQ                                          h9t8xfw
OmJfDMQ/2ODR                                 P9UsMz+q
fDZ28L/U                                     6+y/2FL1AgkG9D/gv/97MVJEP+i9
aaXjO7IgP9qU                                 u5s8Cri/4flbnB86
K9+5bvS/4TV5YHmi                             ML/hfd4n
3D8                                          L4DQP+pOmA
4haKX6kNfA                                   c7Q
v+tJ                                         7A
6fKZS54/                                     fL/uoqA
03qhEIk                                      pqPa8L/iMA
Z/S/3g                                       pTojOQ
ug                                           Tj/pIqR4Xz0KP+lq
NL74xg                                       Vz8
uL/bLCRvWKDIP+Vlzn3iQ1K/1tmeDQ               Ig
YjloP9lOPY9yLw                               zqA
WD/gNVEEIg                                   P+yo9vsKUeg/ysb5ia4
ENA                                          nNg/
P+d+                                         3yA
ezk                                          7TVVCQ
2jDCv8z0lEJ1iLi/2Wkx/Q                       YD/mRwE
2aUsv+OYmtv9                                 EIwvUr/omyTqU4ssP+dIenI
wg                                           lVdm
Mr/pMg                                       P+s
7u56MXi/6tqGbjxlzg                           iVw
P+cg9no                                      vZtuPD/kEB98pGk
u4aSP9gpVnBPXHw                              SL/VJYc
v+gbp89hoQ                                   R4QnTA
nj8                                          vw
6A                                           6SGETgTW
95g                                          7D/YZTDXfNxgP+zU
cPEY                                         /vot/Bi/0AI
7j/exKMBtKxAP+FZx3MuzA                       G2aaQRg/xSe6OaDYaA
```

Decoded Input:

```
00000000: 0101 0201 0500 0000 0503 0204 1610 083f  ...............?
00000010: b999 9999 9999 9a3f c999 9999 9999 9a3f  .......?.......?
00000020: d333 3333 3333 333f d999 9999 9999 9a3f  .333333?.......?
00000030: e000 0000 0000 003f e333 3333 3333 333f  .......?.333333?
00000040: e666 6666 6666 663f e999 9999 9999 9a05  .ffffff?........
00000050: 0000 0080 100a bfcf bc7f b896 a7e8 3fd3  ..............?.
00000060: 140b cf16 36c0 bfe2 a77d b387 2e84 bfe3  ....6....}......
00000070: f122 86e4 e268 3fd1 5eb0 f12c 3ba0 3fb3  ."...h?.^..,;.?.
00000080: cc75 6e56 a040 bfee d266 5697 c3c8 bfe8  .unV.@...fV.....
00000090: e127 7c85 572c bfe9 ea33 fbe4 5716 3fe3  .'|.W,...3..W.?.
000000a0: bad0 6fe7 83a2 0500 0000 8010 f53f b004  ..o..........?..
000000b0: e4e1 da0b e0bf df6d 1b8d 1f67 d43f e689  .......m...g.?..
000000c0: a8d1 77ae e2bf d301 13af 0b83 f83f ca26  ..w..........?.&
000000d0: a65d 86c1 e83f d584 49a1 f933 dcbf b83a  .]...?..I..3...:
000000e0: 2aa8 2856 10bf e148 4709 22a7 ec3f e2ba  *.(V...HG."..?..
000000f0: 6038 1ec6 b6bf ef6c ba89 91ec 883f ebb9  `8.....l.....?..
00000100: 05b6 8f45 4ebf d0f0 315f ae43 f4bf ebe1  ...EN...1_.C....
00000110: dfb2 0a73 b6bf ee4e 33af 0b60 963f da1a  ...s...N3..`.?..
00000120: 921f 46bc 64bf 94d8 83f2 3df9 00bf 997a  ..F.d.....=....z
00000130: d319 1312 803f dae9 208e d0fd 78bf d191  .....?.. ...x...
00000140: 97f6 73ef 0cbf d025 0c4a c3cb e4bf e140  ..s....%.J.....@
00000150: 5797 7cb1 84bf dcd8 f12e 839c b0bf d451  W.|............Q
00000160: 37cd 60a1 a8bf e28d 5c35 b7ce 1c3f a577  7.`.....\5...?.w
00000170: e5d8 1f81 a03f d897 88ff f94b 6c3f be10  .....?.....Kl?..
00000180: b181 ad85 e03f d6d1 733f 8388 183f ebdf  .....?..s?...?..
00000190: 1d94 e13e b63f ed6e 824e c7e1 7c3f ec5e  ...>.?.n.N..|?.^
000001a0: c7ad 89d7 163f d7c1 6a0f 7eb2 fc3f e901  .....?..j.~..?..
000001b0: 11da 9adf 343f bace 1aa1 8ddc d03f e3c1  ....4?.......?..
000001c0: 8dbe 3b2e 923f 8553 49e2 761e 80bf ee05  ..;..?.SI.v.....
000001d0: 4cce 8135 e03f e4be 9663 7f72 003f ebfb  L..5.?...c.r.?..
000001e0: 0b91 c92b c63f e335 4d80 939b 38bf c69b  ...+.?.5M...8...
000001f0: b165 4c7c 68bf e5cf c54d e496 46bf c729  .eL|h....M..F..)
00000200: b145 ea4f e03f ecfd d392 c79c 5abf ebd9  .E.O.?......Z...
00000210: 149b c39b 68bf cc14 4d24 a46b 70bf c867  ....h...M$.kp..g
00000220: 1cf3 5498 b8bf d961 3ceb c99c 5cbf e8bb  ..T....a<...\...
00000230: e15e 1ca1 d2bf df5a e3ba dcaa 203f dcda  .^.....Z.... ?..
00000240: 05f4 a921 38bf e1b7 be57 3dcf dcbf ea7c  ...!8....W=....|
00000250: 3097 ed4d 243f ddec a4ca b93f e03f cf90  0..M$?.....?.?..
00000260: 793c 563a d83f dc43 7c39 53b5 8cbf eea4  y<V:.?.C|9S.....
00000270: e4b1 9e72 ecbf daa3 3460 b822 08bf d8be  ...r....4`."....
00000280: d0f8 66cb 20bf 97d1 9bb0 9350 003f bd43  ..f. ......P.?.C
00000290: eabf 36e0 503f d18c b530 155b d03f e08a  ..6.P?...0.[.?..
000002a0: ad8b c71c 243f cd00 a38b ee3e 30bf b223  ....$?.....>0..#
000002b0: baaa 6bde c0bf eb7e 438e c85f 4abf dc84  ..k....~C.._J...
000002c0: 83d5 7955 103f e8ca 604a fde3 7c3f e4bd  ..yU.?..`J..|?..
000002d0: 1bb8 f153 ea3f d554 addb 0460 483f e734  ...S.?.T...`H?.4
000002e0: c7e5 0afc 503f c539 b6d0 3a91 78bf e673  ....P?.9..:.x..s
000002f0: 3059 8283 1e3f d223 fe22 cc66 48bf efb8  0Y...?.#.".fH...
00000300: 4a58 346a 2a3f e64d 14f4 88cb 743f dc71  JX4j*?.M....t?.q
00000310: cbbd 941a c0bf e1a9 0bd4 25f8 363f e9d4  ..........%.6?..
00000320: c809 d26d e8bf e418 9aa8 fa2e 76bf e564  ...m........v..d
00000330: 3a62 5f0c c43f d8e0 d17c 3676 f0bf d469  :b_..?...|6v...i
00000340: a5e3 3bb2 203f da94 2bdf b96e f4bf e135  ..;. ?..+..n...5
00000350: 7960 79a2 dc3f e216 8a5f a90d 7cbf eb49  y`y..?..._..|..I
00000360: e9f2 994b 9e3f d37a a110 8967 f4bf deba  ...K.?.z...g....
00000370: 34be f8c6 b8bf db2c 246f 58a0 c83f e565  4......,$oX..?.e
00000380: ce7d e243 52bf d6d9 9e0d 6239 683f d94e  .}.CR.....b9h?.N
00000390: 3d8f 722f 583f e035 5104 2210 d03f e77e  =.r/X?.5Q."..?.~
000003a0: 7b39 da30 c2bf ccf4 9442 7588 b8bf d969  {9.0.....Bu....i
000003b0: 31fd d9a5 2cbf e398 9adb fdc2 32bf e932  1...,.......2..2
000003c0: eeee 7a31 78bf eada 866e 3c65 ce3f e720  ..z1x....n<e.?. 
000003d0: f67a bb86 923f d829 5670 4f5c 7cbf e81b  .z...?.)VpO\|...
000003e0: a7cf 61a1 9e3f e8f7 9870 f118 ee3f dec4  ..a..?...p...?..
000003f0: a301 b4ac 403f e159 c773 2ecc 263f e149  ....@?.Y.s..&?.I
00000400: 5596 726f 123f dd3b e359 402e b83f d6dc  U.ro.?.;.Y@..?..
00000410: 17a5 6e82 b0bf e100 ef6f 4801 90bf e669  ..n......oH....i
00000420: 7cd6 d368 ea3f e97c 4ee5 ce3a 36bf e5f9  |..h.?.|N..:6...
00000430: b2dc cbdf 5abf c8d2 f1ea 16d8 70bf e53c  ....Z.......p..<
00000440: 7d4f 8a31 96bf dddc fd2a ef4b 0cbf dc84  }O.1.....*.K....
00000450: 87a8 f826 743f ef22 10d4 e12d a0bf e41c  ...&t?."...-....
00000460: 4202 8fa9 24bf d42a e546 b797 0cbf ec65  B...$..*.F.....e
00000470: 0676 6803 223f e2dd e8c2 c254 4c3f bafb  .vh."?.....TL?..
00000480: ac58 5d5f f0bf ec73 7573 c4d2 04bf e80b  .X]_...sus......
00000490: 78ae 2c77 be3f df16 197c 693b c43f eec2  x.,w.?...|i;.?..
000004a0: ad29 d33c 1a3f c401 91d6 533d 80bf e01c  .).<.?....S=....
000004b0: 96bf c1aa 4c3f ec5f b716 f118 e8bf e430  ....L?._.......0
000004c0: e245 fa3f 4a3f d210 7e9d 4604 18bf bea2  .E.?J?..~.F.....
000004d0: d0dd c850 80bf e4f2 bc84 5e3e 163f e481  ...P......^>.?..
000004e0: e03f 8745 9abf 8007 684b 25be 003f e68a  .?.E....hK%..?..
000004f0: 8a0d 6184 60bf cad2 389a bffd 68bf e10a  ..a.`...8...h...
00000500: efe3 1021 e0bf c1fe e1db 73d4 a8bf d51f  ...!......s.....
00000510: c600 acb2 e0bf e948 50d9 9625 2cbf e01a  .......HP..%,...
00000520: 21e4 49d5 da3f dafe 9f69 d224 5cbf c855  !.I..?...i.$\..U
00000530: cf62 ce4e c8bf ed47 19fa e7b6 3ebf e325  .b.N...G....>..%
00000540: 79e3 2a0c ccbf e938 8a05 4db5 96bf e030  y.*....8..M....0
00000550: fad2 fe4d 183f d4f1 103b a7f3 a43f e232  ...M.?...;...?.2
00000560: d22a 1cc7 6cbf e4c6 7dea a1d7 a23f e455  .*..l...}....?.U
00000570: 4270 7a57 12bf bc22 947b 7500 a03f e37c  BpzW...".{u..?.|
00000580: 7f04 adcb c83f b92c 9a1d b8d1 103f e0b8  .....?.,.....?..
00000590: 8661 0dbc 00bf e529 ae27 3756 503f c26b  .a.....).'7VP?.k
000005a0: e507 6840 083f e4db 1092 a43f 66bf ef67  ..h@.?.....?f..g
000005b0: cdc4 8201 dcbf eeee 2b43 4a6e 023f e65b  ........+CJn.?.[
000005c0: 44b7 a8a1 da3f ec25 f627 a640 90bf e1d6  D....?.%.'.@....
000005d0: 34cf dd8b 243f c8b7 161e 162c 80bf d5a9  4...$?.....,....
000005e0: a307 3d6b 103f dce0 c854 a42e 603f c171  ..=k.?...T..`?.q
000005f0: 74ea f58a 683f d878 c76c 344d 1c3f e4cd  t...h?.x.l4M.?..
00000600: 88d3 2244 8e3f b6fe 2b7d ff84 50bf de70  .."D.?..+}..P..p
00000610: c84a 4d8b 943f e47e 682d 83fb 94bf e6c5  .JM..?.~h-......
00000620: 0d42 8ca0 debf c202 4ff2 d3d1 303f dc73  .B......O...0?.s
00000630: 6115 be81 0c3f e673 8cce 87a7 34bf dbe9  a....?.s....4...
00000640: 85c9 dc92 003f ef5b 3446 4ee2 c4bf c738  .....?.[4FN....8
00000650: a52b 1c57 20bf dbfc e242 f923 f0bf d603  .+.W ....B.#....
00000660: 0d99 723c 583f 7e56 d72d cc50 00bf d476  ..r<X?~V.-.P...v
00000670: 1157 bb03 c43f ef72 be68 c42d eabf ef6a  .W...?.r.h.-...j
00000680: 8bef 838b 923f de3e ad3a 7cd1 c0bf d727  .....?.>.:|....'
00000690: 7b83 6c19 30bf e243 7b8c 81eb 00bf e6d2  {.l.0..C{.......
000006a0: 99cf ab06 e2bf e1f0 15b7 bf4e a43f de47  ...........N.?.G
000006b0: ffe4 e51e 28bf de74 6ea3 cf2f ccbf e1e3  ....(..tn../....
000006c0: 0731 b5a9 b6bf adb8 76f7 5f87 60bf a6de  .1......v._.`...
000006d0: a536 b9e3 80bf cb60 743e 171e f8bf d842  .6.....`t>.....B
000006e0: 1826 6ab8 ec3f d4c3 f44d 51a7 b03f ec79  .&j..?...MQ..?.y
000006f0: fef9 8e23 70bf e1e9 b915 08ec 6cbf d8dd  ...#p.......l...
00000700: ae12 1cfc 543f d0be 07fe 54c3 903f af42  ....T?....T..?.B
00000710: 9979 02ab c0bf e506 0a6b 57ac dc3f d840  .y.......kW..?.@
00000720: a637 55ef 5cbf edea bbfb 4743 08bf d04d  .7U.\.....GC...M
00000730: c758 a4fb 9c3f e610 4ebb b164 68bf ebb3  .X...?..N..dh...
00000740: 0ca5 ef97 cebf e66a bf0c 0566 723f d946  .......j...fr?.F
00000750: 68d4 2f11 d03f b8bd 23f5 1294 c03f d7cd  h./..?..#....?..
00000760: 83d9 dd5d 243f d248 6707 3a9f 78bf d00c  ...]$?.Hg.:.x...
00000770: 37db 0fec d03f de8e 2737 df58 8c3f d85b  7....?..'7.X.?.[
00000780: 0170 80ab 74bf d399 87db 7cc5 fc3f d52c  .p..t.....|..?.,
00000790: 333f aaeb ecbf d852 f502 0906 f43f e0bf  3?.....R.....?..
000007a0: ff7b 3152 443f e8bd bb9b 3c0a b8bf e1f9  .{1RD?....<.....
000007b0: 5b9c 1f3a 30bf e17d de27 2f80 d03f ea4e  [..:0..}.'/..?.N
000007c0: 9873 b4ec 7cbf eea2 a0a6 a3da f0bf e230  .s..|..........0
000007d0: a53a 2339 4e3f e922 a478 5f3d 0a3f e96a  .:#9N?.".x_=.?.j
000007e0: 573f 22ce a03f eca8 f6fb 0a51 e83f cac6  W?"..?.....Q.?..
000007f0: f989 ae9c d83f df20 ed35 5509 603f e647  .....?. .5U.`?.G
00000800: 0110 8c2f 52bf e89b 24ea 538b 2c3f e748  .../R...$.S.,?.H
00000810: 7a72 9557 663f eb89 5cbd 9b6e 3c3f e410  zr.Wf?..\..n<?..
00000820: 1f7c a469 48bf d525 8747 8427 4cbf e921  .|.iH..%.G.'L..!
00000830: 844e 04d6 ec3f d865 30d7 7cdc 603f ecd4  .N...?.e0.|.`?..
00000840: fefa 2dfc 18bf d002 1b66 9a41 183f c527  ..-......f.A.?.'
00000850: ba39 a0d8 68                             .9..h
```

Disassembled Input:

```
SLAT  1
SUAT  1
SWS   5
SLPT  2
SUPT 22
NEW_SAMPLES 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8
SWS 128
NEW_SAMPLES
    -0.24794003022299127
     0.29809851859395664
    -0.5829456812293334
    -0.6231854090356821
     0.27140449096708075
     0.07733854240234539
    -0.9631835643068536
    -0.7774846488998484
    -0.8098392410053943
     0.6165544686920053
SWS 128  # <- DOES NOT IMPLY A `RESET`
NEW_SAMPLES
     0.06257467760046564
    -0.4910344007636216
     0.7043041316187237
    -0.29694072813259664
     0.20430450026243752
     0.3361991960308026
    -0.09463755231293924
    -0.540072934954194
     0.5852509590242423
    -0.9820225417055477
     0.8663357320421399
    -0.26466020911999455
    -0.8713224866256641
    -0.9470461291157501
     0.40787175230338435
    -0.020357190761836286
    -0.024882601170946206
     0.42047895380888844
    -0.2745113283888123
    -0.25226123143437307
    -0.5391042669994452
    -0.4507410959472038
    -0.3174571519507716
    -0.5797558831386058
     0.041930372841082475
     0.38424897191469287
     0.11744222084009648
     0.3565338249446781
     0.8709857852754428
     0.9197398699462123
     0.8865698232100125
     0.37118007195640224
     0.7813805837276733
     0.10470739788239602
     0.6173771586849901
     0.010412766669801288
    -0.9381469758315539
     0.6482650702778869
     0.8743951651934985
     0.6002566825162381
    -0.17662637182454266
    -0.6816126366945319
    -0.18095985330421538
     0.905984675101432
    -0.8702490846888908
    -0.2193695477406794
    -0.19064676171655548
    -0.39655993486525687
    -0.7729346120950658
    -0.4899224591087279
     0.4508070840133942
    -0.5536796287474277
    -0.8276598899196057
     0.4675685863230665
     0.24659648367056408
     0.4416189727624775
    -0.9576285809631293
    -0.41621121831170216
    -0.38664650209391205
    -0.023260529186543977
     0.11431758087462751
     0.27421312041900325
     0.5169284563097603
     0.22658199627447706
    -0.07085768376043244
    -0.8591630734181106
    -0.44558807227197494
     0.7747041191752113
     0.6480845081483697
     0.33329340351474857
     0.7251929734701523
     0.165823795007906
    -0.7015611408461131
     0.2834468211964105
    -0.9912463877438473
     0.6969094062863932
     0.4444455481865752
    -0.5518855231782769
     0.8072242919765218
    -0.6280034351670583
    -0.6684848710359792
     0.38872182016517254
    -0.31894824209919825
     0.4152936634834383
    -0.5377776035575965
     0.5652515285841413
    -0.8527726877458581
     0.3043596898547769
    -0.48011511468494517
    -0.4245692336430804
     0.6686775644940133
    -0.35703231150627923
     0.39540041931535574
     0.5065083580707554
     0.734189618103777
    -0.22621396298479168
    -0.397045610333026
    -0.6123785301879876
    -0.7874674470672707
    -0.8391754296346166
     0.722773780548055
     0.3775230500008957
    -0.7533759165208271
     0.7802240568060179
     0.48075175444200013
     0.5422093629516709
     0.5402019442003356
     0.45678027835740975
     0.357183372072579
    -0.5313641713583355
    -0.700376910764388
     0.7964243400945807
    -0.6867307960919604
    -0.19393752985132862
    -0.6636339715492336
    -0.46661309426160424
    -0.44558898449813644
     0.9729084165386901
    -0.6284494447730009
    -0.3151181402775911
    -0.8873321831343655
     0.5895885280502937
     0.10540272862760935
    -0.8890940915212586
    -0.7514003183202858
     0.4857238497688139
     0.9612642113587555
     0.15629790272803845
    -0.5034898514980539
     0.8866839836198581
    -0.6309672705410574
     0.2822567497133277
    -0.11967187323199546
    -0.6546309075656065
     0.6408540001668144
    -0.007826628487889842
     0.7044115315767492
    -0.20954043918753062
    -0.5325850901436375
    -0.14059088912441564
    -0.33006429735068643
    -0.7900776147591038
    -0.5031899889715377
     0.42179093679493973
    -0.19011871647363976
    -0.9149293804636682
    -0.5983247219850454
    -0.7881517509064675
    -0.5059789772953165
     0.32721334291255233
     0.5687037298687136
    -0.6492299635562981
     0.6354076573213396
    -0.10990264906013403
     0.6089472857842049
     0.09833682275422384
     0.5225250144557094
    -0.661337925523819
     0.143917683235941
     0.651741300973282
    -0.9814213598293082
    -0.9665733637115752
     0.6986411654552811
     0.8796339773562227
    -0.5573982295867137
     0.1930873534114177
    -0.33847881037733973
     0.45121963754420413
     0.13627492401708996
     0.38237176482034996
     0.6500896571834731
     0.08981582475782202
    -0.4756336904157987
     0.6404305352187856
    -0.7115541744033427
    -0.14069556576544917
     0.44454218982174676
     0.7016052278315557
    -0.43612808907553813
     0.9798833249288568
    -0.181416173982762
    -0.4373098043475343
    -0.34393634781821936
     0.007407036345075113
    -0.31970628325876427
     0.9827568098275468
    -0.9817561796192982
     0.472575480572484
    -0.3617848189754964
    -0.5707376236235575
    -0.7132081085221353
    -0.5605572308363276
     0.4731445060064936
    -0.4758564567280217
    -0.5589633913889915
    -0.05804797906581771
    -0.04466739934009123
    -0.2138810446906445
    -0.3790340781369099
     0.3244601016109483
     0.8898920892835189
    -0.5597806368672429
    -0.3885302712332692
     0.261598585481857
     0.06105498888185634
    -0.6569873901875343
     0.37894587901950216
    -0.9349040897160146
    -0.2547472348850819
     0.689490667903681
    -0.8656066170631165
    -0.70053055141325
     0.3949224540813505
     0.0966360543557867
     0.3719186427674279
     0.28566909509617444
    -0.2507457389144294
     0.47742634254735417
     0.38055454241355524
    -0.30624576982799545
     0.33082276551766543
    -0.38006329725986565
     0.5234372526270552
     0.7731607467579442
    -0.5616891907937482
    -0.546614719900413
     0.8220941791436327
    -0.9573519949616109
    -0.5684381614208094
     0.785478816129314
     0.7942310555576633
     0.8956255820399379
     0.2091972276950631
     0.48638467987270495
     0.6961674998469596
    -0.7689385010420202
     0.7275974500614495
     0.8605178550018944
     0.6269681391161521
    -0.33041555389410315
    -0.7853414081389167
     0.3811761955616415
     0.9010004888840539
    -0.2501286031702121
     0.16527488531000079
```

Example Output:

```
      5: 0.250
      6: 0.350
      7: 0.450
      8: 0.550
    128: -0.221
    129: -0.225
    130: -0.231
    131: -0.234
    132: -0.223
    133: -0.224
    134: -0.234
    135: -0.232
    136: -0.219
    137: -0.205
    138: -0.209
    139: -0.215
    140: -0.204
    141: -0.216
    142: -0.210
    143: -0.214
    144: -0.224
    145: -0.218
    146: -0.212
    147: -0.212
    148: -0.204
    149: -0.215
    150: -0.214
    151: -0.208
    152: -0.207
    153: -0.216
    154: -0.212
    155: -0.213
    156: -0.227
    157: -0.231
    158: -0.236
    159: -0.236
    160: -0.228
    161: -0.219
    162: -0.220
    163: -0.215
    164: -0.220
    165: -0.215
    166: -0.218
    167: -0.218
    168: -0.231
    169: -0.235
    170: -0.233
    171: -0.248
    172: -0.260
    173: -0.260
    174: -0.254
    175: -0.250
    176: -0.254
    177: -0.263
    178: -0.263
    179: -0.260
    180: -0.249
    181: -0.242
    182: -0.246
    183: -0.242
    184: -0.234
    185: -0.240
    186: -0.237
    187: -0.224
    188: -0.214
    189: -0.223
    190: -0.212
    191: -0.205
    192: -0.215
    193: -0.221
    194: -0.225
    195: -0.219
    196: -0.209
    197: -0.215
    198: -0.210
    199: -0.215
    200: -0.223
    201: -0.236
    202: -0.244
    203: -0.239
    204: -0.235
    205: -0.236
    206: -0.242
    207: -0.248
    208: -0.254
    209: -0.263
    210: -0.261
    211: -0.249
    212: -0.257
    213: -0.251
    214: -0.254
    215: -0.258
    216: -0.259
    217: -0.260
    218: -0.263
    219: -0.259
    220: -0.258
    221: -0.264
    222: -0.275
    223: -0.266
    224: -0.270
    225: -0.257
    226: -0.257
    227: -0.255
    228: -0.245
    229: -0.246
    230: -0.246
    231: -0.247
    232: -0.256
    233: -0.256
    234: -0.248
    235: -0.250
    236: -0.249
    237: -0.236
    238: -0.237
    239: -0.248
    240: -0.247
    241: -0.234
    242: -0.234
    243: -0.237
    244: -0.237
    245: -0.237
    246: -0.250
    247: -0.248
    248: -0.237
    249: -0.225
    250: -0.234
    251: -0.235
    252: -0.229
    253: -0.216
    254: -0.214
    255: -0.208
```

#### Parameter Limits

 - Number of formatted input lines: >= 1 and <= 300,000
 - Number of encoded segments: >= 1 and <= 300,000
 - Window Size: >= 0 and <= 100,000
 - `n_abs`: >= 0 and <= 255
 - `n_prop`: >= 0 and <= 100
 - every sample: >= -10,000 and <= 10,000

#### Considerations and Review Criteria

No submissions using third-party packages.  All submissions are limited strictly to
CPython 3.12 and the standard library included with it.

Submissions are judged primarily by the extent to which they accurately comply with these
specifications and guidelines.  Special considerations are given to compliant submissions
with performance characteristics that scale well within the prescribed limits.  Auxillary
development products, such as tests, simulations, scripts, and similar code fixtures are
also taken into consideration.  Code quality, documentation, and developer notes are also
greatly appreciated and considered favorably.

Please provide additional commentary with context, considerations, and assumptions made,
including any limitations, trade-offs, or other important design decisions.  Include any
questions that need to be answered to ensure a correct and reliable design, or any other
notes that could help orient reviewers of your submission.  Your submission must include
all necessary files and documentation.  Your submission must be provided as a compressed
folder.
