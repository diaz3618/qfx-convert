"""Tests for CLI functionality."""

import pytest
import sys
from pathlib import Path
from io import StringIO

from qfxconvert.cli import parse_args, main


TEST_DATA_DIR = Path(__file__).parent / "data"


class TestParseArgs:
    """Test cases for argument parsing."""
    
    def test_default_format_is_csv(self):
        """Test that default format is CSV."""
        args = parse_args(['test.ofx'])
        assert args.format == 'csv'
    
    def test_csv_flag(self):
        """Test --csv flag."""
        args = parse_args(['--csv', 'test.ofx'])
        assert args.format == 'csv'
    
    def test_json_flag(self):
        """Test --json flag."""
        args = parse_args(['--json', 'test.ofx'])
        assert args.format == 'json'
    
    def test_csv_and_json_mutually_exclusive(self):
        """Test that --csv and --json cannot be used together."""
        with pytest.raises(SystemExit):
            parse_args(['--csv', '--json', 'test.ofx'])
    
    def test_output_flag(self):
        """Test -o/--output flag."""
        args = parse_args(['-o', 'output.csv', 'test.ofx'])
        assert args.output == 'output.csv'
        
        args = parse_args(['--output', 'output.csv', 'test.ofx'])
        assert args.output == 'output.csv'
    
    def test_compact_flag(self):
        """Test --compact flag."""
        args = parse_args(['--compact', 'test.ofx'])
        assert args.compact is True
    
    def test_quiet_flag(self):
        """Test -q/--quiet flag."""
        args = parse_args(['-q', 'test.ofx'])
        assert args.quiet is True
        
        args = parse_args(['--quiet', 'test.ofx'])
        assert args.quiet is True
    
    def test_multiple_input_files(self):
        """Test multiple input files."""
        args = parse_args(['file1.ofx', 'file2.ofx', 'file3.qfx'])
        assert len(args.input_files) == 3
        assert 'file1.ofx' in args.input_files
        assert 'file2.ofx' in args.input_files
        assert 'file3.qfx' in args.input_files
    
    def test_version_flag(self):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(['--version'])
        assert exc_info.value.code == 0


class TestCLIMain:
    """Test cases for main CLI function."""
    
    def test_successful_csv_conversion(self, tmp_path, monkeypatch):
        """Test successful CSV conversion."""
        import shutil
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "test.ofx"
        shutil.copy(test_file, input_file)
        
        # Mock sys.argv
        monkeypatch.setattr(sys, 'argv', ['qfx-convert', str(input_file)])
        
        # Run main
        exit_code = main()
        
        assert exit_code == 0
        assert (tmp_path / "test.csv").exists()
    
    def test_successful_json_conversion(self, tmp_path, monkeypatch):
        """Test successful JSON conversion."""
        import shutil
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "test.ofx"
        shutil.copy(test_file, input_file)
        
        monkeypatch.setattr(sys, 'argv', ['qfx-convert', '--json', str(input_file)])
        
        exit_code = main()
        
        assert exit_code == 0
        assert (tmp_path / "test.json").exists()
    
    def test_nonexistent_file(self, monkeypatch, capsys):
        """Test handling of non-existent file."""
        monkeypatch.setattr(sys, 'argv', ['qfx-convert', 'nonexistent.ofx'])
        
        exit_code = main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'not found' in captured.err.lower()
    
    def test_multiple_files_with_single_output_error(self, monkeypatch, capsys):
        """Test error when specifying single output with multiple inputs."""
        monkeypatch.setattr(sys, 'argv', [
            'qfx-convert',
            '-o', 'output.csv',
            'file1.ofx',
            'file2.ofx'
        ])
        
        exit_code = main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert 'multiple input files' in captured.err.lower()
    
    def test_quiet_mode_suppresses_output(self, tmp_path, monkeypatch, capsys):
        """Test that quiet mode suppresses informational output."""
        import shutil
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "test.ofx"
        shutil.copy(test_file, input_file)
        
        monkeypatch.setattr(sys, 'argv', ['qfx-convert', '-q', str(input_file)])
        
        exit_code = main()
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out == ''  # No output in quiet mode
    
    def test_custom_output_file(self, tmp_path, monkeypatch):
        """Test conversion with custom output file."""
        import shutil
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "test.ofx"
        output_file = tmp_path / "custom_output.csv"
        shutil.copy(test_file, input_file)
        
        monkeypatch.setattr(sys, 'argv', [
            'qfx-convert',
            '-o', str(output_file),
            str(input_file)
        ])
        
        exit_code = main()
        
        assert exit_code == 0
        assert output_file.exists()
    
    def test_compact_json_output(self, tmp_path, monkeypatch):
        """Test compact JSON output."""
        import shutil
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "test.ofx"
        shutil.copy(test_file, input_file)
        
        monkeypatch.setattr(sys, 'argv', [
            'qfx-convert',
            '--json',
            '--compact',
            str(input_file)
        ])
        
        exit_code = main()
        
        assert exit_code == 0
        output_file = tmp_path / "test.json"
        assert output_file.exists()
        
        # Check that output is compact (fewer lines)
        with open(output_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            assert len(lines) < 10  # Compact should have few lines


class TestCLIIntegration:
    """Integration tests for the full CLI workflow."""
    
    def test_end_to_end_csv(self, tmp_path):
        """Test complete CSV conversion workflow."""
        import shutil
        import csv
        
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "statement.ofx"
        shutil.copy(test_file, input_file)
        
        # Simulate CLI call
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ['qfx-convert', str(input_file)]
            exit_code = main()
            
            assert exit_code == 0
            output_file = tmp_path / "statement.csv"
            assert output_file.exists()
            
            # Verify CSV content
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0
                assert 'trnamt' in rows[0]
        finally:
            sys.argv = old_argv
    
    def test_end_to_end_json(self, tmp_path):
        """Test complete JSON conversion workflow."""
        import shutil
        import json
        
        test_file = TEST_DATA_DIR / "stmtrs-160.ofx"
        input_file = tmp_path / "statement.ofx"
        shutil.copy(test_file, input_file)
        
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ['qfx-convert', '--json', str(input_file)]
            exit_code = main()
            
            assert exit_code == 0
            output_file = tmp_path / "statement.json"
            assert output_file.exists()
            
            # Verify JSON content
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert 'transactions' in data
                assert len(data['transactions']) > 0
        finally:
            sys.argv = old_argv
