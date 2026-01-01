# qfx-convert

Convert QFX/OFX bank statements to CSV or JSON from the command line.

## Features

- Convert to CSV or JSON
- Handles large files (10MB+) efficiently  
- Preserves decimal precision and date formats
- Supports international characters in merchant names
- Process multiple files at once
- Compact or pretty-printed JSON output

## Installation

### From Source

```bash
git clone https://github.com/diaz3618/qfx-convert.git
cd qfx-convert
pip install -e .
```

Requires Python 3.8+ and ofxtools 0.9.5+

## Usage

Convert to CSV (default):
```bash
qfx-convert transactions.qfx
```

Convert to JSON:
```bash
qfx-convert transactions.qfx --json
```

### Options

```
qfx-convert [OPTIONS] INPUT_FILE [INPUT_FILE ...]

Options:
  --csv                   Convert to CSV (default)
  --json                  Convert to JSON
  -o, --output PATH       Output file (defaults to input filename)
  --compact               Minified JSON
  -q, --quiet             Suppress output messages
  -v, --version           Show version
  -h, --help              Show help
```

### Examples

**Single file:**
```bash
qfx-convert statement.qfx
```

**Custom output:**
```bash
qfx-convert statement.qfx --json -o my-transactions.json
```

**Multiple files:**
```bash
qfx-convert jan-2025.qfx feb-2025.qfx mar-2025.qfx
```

**Minified JSON:**
```bash
qfx-convert statement.qfx --json --compact
```

## Output Format

CSV columns:
- `account_id` - Account number
- `account_type` - CHECKING, SAVINGS, etc.
- `bank_id` - Routing number
- `dtposted` - Transaction date (ISO 8601)
- `fitid` - Unique transaction ID
- `memo` - Description
- `name` - Merchant/payee
- `trnamt` - Amount (negative for debits)
- `trntype` - DEBIT, CREDIT, etc.

JSON structure:
```json
{
  "transactions": [
    {
      "account_id": "7960356199",
      "account_type": "CHECKING",
      "bank_id": "256074974",
      "dtposted": "2025-12-31T12:00:00+00:00",
      "fitid": "8a34b44c9b1ca9e5019b7854a49b6d15",
      "memo": "Dividend",
      "name": "Dividend",
      "trnamt": 0.01,
      "trntype": "CREDIT"
    }
  ]
}
```

## Performance

Tested with a 1.2MB file (5,085 transactions) in ~10 seconds. Should handle 10MB+ files without issues.

## Encoding

International characters (like "Café" or "Taquería") are automatically normalized to ASCII equivalents. All transaction amounts and IDs are preserved exactly.

## Development

Run tests:
```bash
pytest tests/ -v
```

Test coverage:
```bash
pytest tests/ --cov=qfxconvert --cov-report=html
```

## Troubleshooting

**Parse errors:** Make sure the file is valid QFX/OFX format. Try opening it in a text editor to verify it's not corrupted.

**Missing transactions:** Some files only contain account info without transactions. Check for `<STMTTRN>` elements.

**Encoding issues:** The tool auto-detects UTF-8 and Latin-1. Non-ASCII characters get normalized but transaction data stays intact.

## License

MIT License - see [LICENSE](LICENSE)
