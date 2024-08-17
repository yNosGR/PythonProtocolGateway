"Protocols" are defined through 2 file types. 

The first is .json, which contains the default settings and optionally codes. 

The .csv files hold the registry or address definitions. 

# CSV

CSV = comma seperated values... spreadsheets. 
delimeter for csv can be , or ; ( not both )

| variable name | data type | register|documented name|description|writable|values |
| -- | -- | -- | -- | -- | -- | -- | 


### variable name
provides a user-friendly name to work with, while retaining the original documented name; since a lot of variable names are up to interpretation. 

### documented name
Original variable name provided from protocol documention; when variable name is not specified, this name is used.

### data type
Defines the expected data type for the register / map entry

| Type | Description |
| -- | -- |
| USHORT | A two byte ( 16 bit ) positive number. For protocols that return 2 byte values, this is the default type. 
| BYTE | A single byte ( 8 bit ) positive number.
| UINT | A four byte ( 32 bit ) positive number. 
| INT | A four byte ( 32 bit ) signed number (positive or negative)
| 16BIT_FLAGS | two bytes split into 16 bits, each bit represents on/off flag which is defined as b#. this will translate into 16x 0/1s if no "codes" are defined. 
| 8BIT_FLAGS | A single byte split into 8 bit flags. see 16BIT_FLAGS
| 32BIT_FLAGS | four bytes split into 32 bit flags. see 16BIT_FLAGS
| #bit | A unsigned number comprised of # of bits. for example, 3bit is a 3 bit positive number (0 to 7). 
| ASCII | ascii text representation of data.
| ASCII.# | for protocols with an undefined "registry" size, the length can be specified. ie: ASCII.7 will return a 7 character long string. 

### register
Register defines the location or for other protocols the main command / id. 
The registers are defined in decimal form. a prefix of "x" is acceptable for hexadecimal. 

For **ASCII** or other MultiRegister Data Types, register ranges can be defined:
```
7~14
```
a prefix of "r" will specify that the registers be "read" in backwards order. 

#### register bit
bit offsets are specified with .b#, # being the bit offset

```
#.b#
```

#### register byte
byte offsets are specified with .#, # being the byte offset

```
#.#
```

#### writable
mainly for registers / entries that support writing, such as the holding register for modbus

```
R = Read Only
RD = Read Disabled
W = Write
```



