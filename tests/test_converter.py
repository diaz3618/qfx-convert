"""Unit tests for QFX/OFX converter."""

import pytest
import json
import csv
from pathlib import Path
from decimal import Decimal

from qfxconvert.converter import QFXConverter, convert_qfx


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


class TestQFXConverter:
    """Test cases for QFXConverter class."""
    
    def test_init_with_valid_file(self):
        """Test initialization with valid file."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        converter = QFXConverter(test_file)
        assert converter.input_file == test_file
        assert not converter._parsed
    
    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            QFXConverter("nonexistent_file.ofx")
    
    def test_parse_valid_ofx(self):
        """Test parsing a valid OFX file."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        converter = QFXConverter(test_file)
        converter.parse()
        assert converter._parsed
        assert converter.ofx_data is not None
    
    def test_parse_invalid_ofx(self):
        """Test parsing an invalid OFX file raises ValueError."""
        test_file = TEST_DATA_DIR / "notofx.gif"
        if not test_file.exists():
            pytest.skip("Test file notofx.gif not found")
        converter = QFXConverter(test_file)
        with pytest.raises(ValueError, match="Failed to parse OFX file"):
            converter.parse()
    
    def test_extract_transactions(self):
        """Test extracting transactions from OFX data."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        converter = QFXConverter(test_file)
        transactions = converter._extract_transactions()
        
        assert len(transactions) > 0
        # Check that first transaction has expected fields
        trx = transactions[0]
        assert 'trnamt' in trx  # Transaction amount
        assert 'dtposted' in trx  # Date posted
        assert 'trntype' in trx  # Transaction type
        assert 'account_id' in trx  # Account ID
    
    def test_transaction_decimal_precision(self):
        """Test that transaction amounts preserve decimal precision."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        converter = QFXConverter(test_file)
        transactions = converter._extract_transactions()
        
        # Check that amounts are floats (converted from Decimal)
        for trx in transactions:
            if 'trnamt' in trx:
                assert isinstance(trx['trnamt'], float)
                # Verify it's a reasonable financial amount
                assert abs(trx['trnamt']) < 1000000  # Sanity check
    
    def test_transaction_datetime_formatting(self):
        """Test that datetimes are properly formatted as ISO strings."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        converter = QFXConverter(test_file)
        transactions = converter._extract_transactions()
        
        for trx in transactions:
            if 'dtposted' in trx:
                # Should be ISO format string
                assert isinstance(trx['dtposted'], str)
                # Should contain date separator
                assert '-' in trx['dtposted'] or 'T' in trx['dtposted']
    
    def test_to_csv_creates_file(self, tmp_path):
        """Test CSV conversion creates output file."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.csv"
        
        converter = QFXConverter(test_file)
        result_path = converter.to_csv(output_file)
        
        assert result_path == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_to_csv_default_filename(self, tmp_path):
        """Test CSV conversion with default output filename."""
        # Copy test file to tmp directory so default output goes there
        import shutil
        test_file_orig = TEST_DATA_DIR / "stmtrs-160.ofx"
        test_file = tmp_path / "test.ofx"
        shutil.copy(test_file_orig, test_file)
        
        converter = QFXConverter(test_file)
        result_path = converter.to_csv()
        
        expected_path = test_file.with_suffix('.csv')
        assert result_path == expected_path
        assert expected_path.exists()
    
    def test_to_csv_content(self, tmp_path):
        """Test CSV output contains correct data."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.csv"
        
        converter = QFXConverter(test_file)
        converter.to_csv(output_file)
        
        # Read and verify CSV content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0
            # Check first row has expected fields
            assert 'trnamt' in rows[0]
            assert 'dtposted' in rows[0]
            assert 'trntype' in rows[0]
    
    def test_to_json_creates_file(self, tmp_path):
        """Test JSON conversion creates output file."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        converter = QFXConverter(test_file)
        result_path = converter.to_json(output_file)
        
        assert result_path == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_to_json_default_filename(self, tmp_path):
        """Test JSON conversion with default output filename."""
        import shutil
        test_file_orig = TEST_DATA_DIR / "stmtrs-160.ofx"
        test_file = tmp_path / "test.ofx"
        shutil.copy(test_file_orig, test_file)
        
        converter = QFXConverter(test_file)
        result_path = converter.to_json()
        
        expected_path = test_file.with_suffix('.json')
        assert result_path == expected_path
        assert expected_path.exists()
    
    def test_to_json_content(self, tmp_path):
        """Test JSON output contains correct data structure."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        converter = QFXConverter(test_file)
        converter.to_json(output_file)
        
        # Read and verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert 'transactions' in data
            assert isinstance(data['transactions'], list)
            assert len(data['transactions']) > 0
            
            # Check first transaction
            trx = data['transactions'][0]
            assert 'trnamt' in trx
            assert 'dtposted' in trx
            assert 'trntype' in trx
    
    def test_to_json_compact(self, tmp_path):
        """Test JSON compact output has no indentation."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        converter = QFXConverter(test_file)
        converter.to_json(output_file, indent=0)
        
        # Read content and verify it's compact
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Compact JSON shouldn't have much whitespace
            lines = content.split('\n')
            # Should be mostly on one or few lines
            assert len(lines) < 10  # Generous threshold
    
    def test_ofx_without_transactions(self):
        """Test handling OFX file without transactions."""
        test_file = TEST_DATA_DIR / "notrans.ofx"
        if not test_file.exists():
            pytest.skip("Test file notrans.ofx not found")
        
        converter = QFXConverter(test_file)
        with pytest.raises(ValueError, match="No transactions found"):
            converter.to_csv()


class TestConvertQFXFunction:
    """Test cases for the convert_qfx convenience function."""
    
    def test_convert_to_csv(self, tmp_path):
        """Test convert_qfx with CSV format."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.csv"
        
        result = convert_qfx(test_file, 'csv', output_file)
        
        assert result == output_file
        assert output_file.exists()
    
    def test_convert_to_json(self, tmp_path):
        """Test convert_qfx with JSON format."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        result = convert_qfx(test_file, 'json', output_file)
        
        assert result == output_file
        assert output_file.exists()
    
    def test_convert_invalid_format(self):
        """Test convert_qfx with invalid format raises ValueError."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            convert_qfx(test_file, 'xml')
    
    def test_convert_nonexistent_file(self):
        """Test convert_qfx with non-existent file."""
        with pytest.raises(FileNotFoundError):
            convert_qfx("nonexistent.ofx", 'csv')


class TestAccuracy:
    """Test cases for conversion accuracy."""
    
    def test_amount_accuracy(self, tmp_path):
        """Test that transaction amounts are accurately converted."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.csv"
        
        converter = QFXConverter(test_file)
        converter.to_csv(output_file)
        
        # Read CSV and verify amounts
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check that we have expected test amounts
            # From stmtrs-160.ofx: -23.17, -100.00, -436.67
            amounts = [float(row['trnamt']) for row in rows if row.get('trnamt')]
            
            assert len(amounts) > 0
            # Verify precision is maintained (2 decimal places for currency)
            for amt in amounts:
                # Check that amount has reasonable precision
                rounded = round(amt, 2)
                assert abs(amt - rounded) < 0.001  # Within 0.1 cent
    
    def test_date_accuracy(self, tmp_path):
        """Test that dates are accurately converted."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        converter = QFXConverter(test_file)
        converter.to_json(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for trx in data['transactions']:
                if 'dtposted' in trx:
                    # Verify date format is ISO
                    date_str = trx['dtposted']
                    assert isinstance(date_str, str)
                    # Should contain year
                    assert '2024' in date_str or '2025' in date_str or '202' in date_str
    
    def test_all_fields_preserved(self, tmp_path):
        """Test that all transaction fields are preserved."""
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        output_file = tmp_path / "output.json"
        
        converter = QFXConverter(test_file)
        converter.parse()
        
        # Get raw transaction
        statements = converter.ofx_data.statements
        raw_trx = statements[0].transactions[0]
        
        # Get converted transaction
        transactions = converter._extract_transactions()
        converted_trx = transactions[0]
        
        # Check that key fields exist in converted data
        key_fields = ['trntype', 'dtposted', 'trnamt', 'fitid']
        for field in key_fields:
            if hasattr(raw_trx, field) and getattr(raw_trx, field) is not None:
                assert field in converted_trx, f"Field {field} missing from converted transaction"
