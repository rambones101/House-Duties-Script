"""Tests for CLI argument parsing."""
import pytest
import sys
import os
from argparse import Namespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties.cli import parse_arguments


class TestCLIParsing:
    """Test command-line argument parsing."""
    
    @pytest.mark.unit
    def test_parse_arguments_defaults(self, monkeypatch):
        """Test parse_arguments with default values."""
        monkeypatch.setattr('sys.argv', ['house_duties.py'])
        args = parse_arguments()
        
        assert args.brothers == "config/brothers.txt"
        assert args.constraints == "constraints.json"
        assert args.weeks == 1
        assert args.start == ""
        assert args.dry_run is False
        assert args.verbose is False
        assert args.quiet is False
    
    @pytest.mark.unit
    def test_parse_arguments_custom_values(self, monkeypatch):
        """Test parse_arguments with custom values."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '--brothers', 'custom.txt',
            '--weeks', '2',
            '--start', '2026-01-25',
            '--dry-run',
            '--verbose'
        ])
        args = parse_arguments()
        
        assert args.brothers == "custom.txt"
        assert args.weeks == 2
        assert args.start == "2026-01-25"
        assert args.dry_run is True
        assert args.verbose is True
    
    @pytest.mark.unit
    def test_parse_arguments_output_options(self, monkeypatch):
        """Test parse_arguments with output options."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '--output-csv', 'custom.csv',
            '--output-json', 'custom.json',
            '--quiet'
        ])
        args = parse_arguments()
        
        assert args.output_csv == "custom.csv"
        assert args.output_json == "custom.json"
        assert args.quiet is True
    
    @pytest.mark.unit
    def test_parse_arguments_seed_option(self, monkeypatch):
        """Test parse_arguments with custom seed."""
        monkeypatch.setattr('sys.argv', [
            'house_duties.py',
            '--seed', '123'
        ])
        args = parse_arguments()
        
        assert args.seed == 123
