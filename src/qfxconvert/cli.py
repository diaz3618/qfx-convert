"""CLI for QFX/OFX converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .converter import QFXConverter


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='qfx-convert',
        description='Convert QFX/OFX files to CSV or JSON format with high accuracy.',
        epilog='For bug reports and feature requests, visit: https://github.com/your-repo/qfx-convert'
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        metavar='FILE',
        help='QFX/OFX file(s) to convert. Supports wildcards (e.g., *.qfx)'
    )
    
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        '--csv',
        action='store_const',
        const='csv',
        dest='format',
        help='Output in CSV format (default)'
    )
    format_group.add_argument(
        '--json',
        action='store_const',
        const='json',
        dest='format',
        help='Output in JSON format'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Output file path (optional). If not specified, uses input filename with appropriate extension'
    )
    
    parser.add_argument(
        '--compact',
        action='store_true',
        help='Compact JSON output (no indentation). Only applies to JSON format.'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress informational output'
    )
    
    parser.set_defaults(format='csv')
    
    return parser.parse_args(args)


def main() -> int:
    args = parse_args()
    
    if args.output and len(args.input_files) > 1:
        print("Error: Cannot specify single output file (-o) with multiple input files",
              file=sys.stderr)
        return 1
    
    success_count = 0
    error_count = 0
    
    for input_file in args.input_files:
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            error_count += 1
            continue
        
        if input_path.is_dir():
            print(f"Warning: Skipping directory: {input_file}", file=sys.stderr)
            continue
        
        try:
            if not args.quiet:
                print(f"Processing {input_file}...")
            
            converter = QFXConverter(input_path)
            output_file = args.output if args.output else None
            
            if args.format == 'json':
                indent = 0 if args.compact else 2
                output_path = converter.to_json(output_file, indent=indent)
            else:
                output_path = converter.to_csv(output_file)
            
            if not args.quiet:
                print(f"  ✓ Created: {output_path}")
                
                if args.format == 'csv':
                    positions_file = output_path.with_suffix('.positions.csv')
                    if positions_file.exists():
                        print(f"  ✓ Created: {positions_file}")
            
            success_count += 1
            
        except FileNotFoundError as e:
            print(f"Error processing {input_file}: {e}", file=sys.stderr)
            error_count += 1
        except ValueError as e:
            print(f"Error processing {input_file}: {e}", file=sys.stderr)
            error_count += 1
        except Exception as e:
            print(f"Unexpected error processing {input_file}: {e}", file=sys.stderr)
            error_count += 1
    
    if not args.quiet and len(args.input_files) > 1:
        print(f"\nProcessed {success_count} file(s) successfully, {error_count} error(s)")
    
    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
