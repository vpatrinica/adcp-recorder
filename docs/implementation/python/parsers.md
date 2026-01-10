[🏠 Home](../../README.md) > [Implementation](../README.md) > Python

# Python Parser Patterns

Common patterns for parsing NMEA sentences into structured data.

## Factory Method Pattern

```python
@classmethod
def from_nmea(cls, sentence: str) -> 'MessageType':
    """Parse NMEA sentence into structured object."""
    sentence = sentence.strip()
    
    # Split sentence and checksum
    if '*' in sentence:
        data_part, checksum = sentence.rsplit('*', 1)
        checksum = checksum.strip().upper()
    else:
        data_part, checksum = sentence, None
    
    # Split fields
    fields = [f.strip() for f in data_part.split(',')]
    
    # Validate field count
    if len(fields) != EXPECTED_FIELD_COUNT:
        raise ValueError(f"Expected {EXPECTED_FIELD_COUNT} fields, got {len(fields)}")
    
    # Validate prefix
    if fields[0] != f"${PREFIX}":
        raise ValueError(f"Invalid identifier: {fields[0]}")
    
    # Parse and validate
    return cls(
        field1=parse_field1(fields[1]),
        field2=parse_field2(fields[2]),
        # ...
        checksum=checksum
    )
```

## Checksum Validation

```python
def compute_checksum(self) -> str:
    """Compute NMEA checksum."""
    sentence_without_checksum = self.to_nmea(include_checksum=False)
    data = sentence_without_checksum[1:]  # Remove leading $
    checksum = 0
    for char in data:
        checksum ^= ord(char)
    return f"{checksum:02X}"

def validate_checksum(self) -> bool:
    """Validate stored checksum."""
    if not self.checksum:
        return False
    return self.compute_checksum().upper() == self.checksum.upper()
```

## Serialization Pattern

```python
def to_nmea(self, include_checksum: bool = True) -> str:
    """Generate NMEA sentence from data."""
    data_fields = [
        f"${PREFIX}",
        str(self.field1),
        f"{self.field2:.2f}",
        # ...
    ]
    
    sentence = ','.join(data_fields)
    
    if include_checksum:
        checksum = self.compute_checksum()
        return f"{sentence}*{checksum}"
    
    return sentence
```

## Auto-Detection Pattern

```python
def parse_nmea_sentence(sentence: str):
    """Auto-detect and parse NMEA sentence type."""
    sentence = sentence.strip()
    
    # Extract prefix
    if not sentence.startswith('$'):
        raise ValueError("Sentence must start with $")
    
    prefix = sentence.split(',')[0][1:]  # Remove $
    
    # Route to appropriate parser
    if prefix == "PNORI":
        return PNORI.from_nmea(sentence)
    elif prefix == "PNORI1":
        return PNORI1.from_sentence(sentence)
    elif prefix == "PNORI2":
        return PNORI2.from_sentence(sentence)
    elif prefix == "PNORS":
        return PNORS.from_sentence(sentence)
    # ... etc
    else:
        raise ValueError(f"Unknown prefix: {prefix}")
```

## Tagged Field Parsing

```python
@classmethod
def parse_tagged_field(cls, field: str) -> tuple[str, str]:
    """Parse TAG=VALUE field."""
    if '=' not in field:
        raise ValueError(f"Tagged field must contain '=': {field}")
    
    tag, value = field.split('=', 1)
    tag = tag.strip().upper()
    
    if tag not in cls.VALID_TAGS:
        raise ValueError(f"Unknown tag: {tag}")
    
    return tag, value.strip()

@classmethod
def from_sentence(cls, sentence: str):
    """Parse tagged sentence."""
    # ... extract fields ...
    
    data = {}
    for field in fields[1:]:  # Skip prefix
        tag, value = cls.parse_tagged_field(field)
        data[tag] = value
    
    # Verify all required tags present
    if set(data.keys()) != cls.VALID_TAGS:
        missing = cls.VALID_TAGS - set(data.keys())
        raise ValueError(f"Missing tags: {missing}")
    
    return cls(
        field1=parse(data['TAG1']),
        field2=parse(data['TAG2']),
        # ...
    )
```

## Related Documents

- [Dataclass Structures](dataclasses.md)
- [Validation Patterns](validation.md)
- [NMEA Checksum](../../nmea/checksum.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
