"""Tests for CLI argument parsing."""
import pytest
import sys
import os
from argparse import Namespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties_legacy import parse_arguments


class TestCLIParsing:
    """Test command-line argument parsing."""
    
    @pytest.mark.unit
    def test_parse_arguments_defaults(self, monkeypatch):
        """Test parse_arguments with default values."""
        monkeypatch.setattr('sys.argv', ['house_duties.py'])
        args = parse_arguments()
        
        assert args.roster == "brothers.txt"
        assert args.constraints == "constraints.json"
        assert args.weeks == 1
        assert args.start_date == ""
        assert args.output_dir == "."
        assert args.dry_run is False
        assert args.verbose is False
        assert args.quiet is False
    
    @pytest.mark.unit
    def test_parse_arguments_custom_values(self, monkeypatch):
        """Test parse_arguments with custom values."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '--roster', 'custom.txt',
            '--weeks', '2',
            '--start-date', '2026-01-25',
            '--dry-run',
            '-v'
        ])
        args = parse_arguments()
        
        assert args.roster == "custom.txt"
        assert args.weeks == 2
        assert args.start_date == "2026-01-25"
        assert args.dry_run is True
        assert args.verbose is True
    
    @pytest.mark.unit
    def test_parse_arguments_invalid_weeks(self, monkeypatch):
        """Test parse_arguments rejects invalid weeks."""
        monkeypatch.setattr('sys.argv', ['house_duties.py', '--weeks', '0'])
        
        with pytest.raises(SystemExit):
            parse_arguments()
    
    @pytest.mark.unit
    def test_parse_arguments_invalid_date(self, monkeypatch):
        """Test parse_arguments rejects invalid date format."""
        monkeypatch.setattr('sys.argv', ['house_duties.py', '--start-date', 'invalid'])
        
        with pytest.raises(SystemExit):
            parse_arguments()
    
    @pytest.mark.unit
    def test_parse_arguments_output_options(self, monkeypatch):
        """Test parse_arguments with output options."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '--output-dir', './output',
            '--output-csv', 'custom.csv',
            '--output-json', 'custom.json',
            '--no-display'
        ])
        args = parse_arguments()
        
        assert args.output_dir == "./output"
        assert args.output_csv == "custom.csv"
        assert args.output_json == "custom.json"
        assert args.no_display is True
    
    @pytest.mark.unit
    def test_parse_arguments_logging_options(self, monkeypatch):
        """Test parse_arguments with logging options."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '-q',
            '--log-file', 'custom.log'
        ])
        args = parse_arguments()
        
        assert args.quiet is True
        assert args.log_file == "custom.log"
    
    @pytest.mark.unit
    def test_parse_arguments_verbose_and_quiet_conflict(self, monkeypatch):
        """Test that both verbose and quiet can be set (quiet takes precedence in configure_logging)."""
        monkeypatch.setattr('sys.argv', ['house_duties.py', '-v', '-q'])
        args = parse_arguments()
        
        # Both flags accepted, configure_logging handles the conflict
        assert args.verbose is True
        assert args.quiet is True
