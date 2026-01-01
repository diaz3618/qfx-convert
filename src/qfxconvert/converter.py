"""QFX/OFX to CSV/JSON converter."""

import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

from ofxtools.Parser import OFXTree


class QFXConverter:
    """Converts QFX/OFX files to CSV or JSON."""

    def __init__(self, input_file: Union[str, Path]):
        self.input_file = Path(input_file)
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        self.ofx_data = None
        self._parsed = False

    def parse(self) -> None:
        try:
            parser = OFXTree()
            with open(self.input_file, 'rb') as f:
                content = f.read()
            
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('latin-1')
                except UnicodeDecodeError:
                    text = content.decode('cp1252', errors='replace')
            
            import unicodedata
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ascii', 'ignore').decode('ascii')
            
            from io import BytesIO
            parser.parse(BytesIO(text.encode('ascii')))
            
            self.ofx_data = parser.convert()
            self._parsed = True
        except Exception as e:
            raise ValueError(f"Failed to parse OFX file: {e}") from e

    def _extract_transactions(self) -> List[Dict[str, Any]]:
        if not self._parsed:
            self.parse()

        transactions = []
        statements = self.ofx_data.statements
        
        for statement in statements:
            account = statement.account
            account_info = {
                'account_id': getattr(account, 'acctid', ''),
                'account_type': getattr(account, 'accttype', ''),
                'bank_id': getattr(account, 'bankid', getattr(account, 'brokerid', '')),
            }
            
            stmt_transactions = statement.transactions
            if stmt_transactions:
                for trx in stmt_transactions:
                    trx_dict = self._transaction_to_dict(trx, account_info)
                    transactions.append(trx_dict)

        return transactions

    def _transaction_to_dict(self, trx: Any, account_info: Dict[str, str]) -> Dict[str, Any]:
        trx_dict = {}
        trx_dict.update(account_info)
        
        for attr_name in dir(trx):
            if attr_name.startswith('_') or callable(getattr(trx, attr_name)):
                continue
                
            attr_value = getattr(trx, attr_name)
            
            if attr_value is None:
                continue
            
            if isinstance(attr_value, datetime):
                trx_dict[attr_name] = attr_value.isoformat()
            elif isinstance(attr_value, Decimal):
                trx_dict[attr_name] = float(attr_value)
            elif isinstance(attr_value, (str, int, float, bool)):
                trx_dict[attr_name] = attr_value
            elif hasattr(attr_value, '__dict__'):
                if hasattr(attr_value, 'uniqueid'):
                    trx_dict[f'{attr_name}_uniqueid'] = attr_value.uniqueid
                if hasattr(attr_value, 'uniqueidtype'):
                    trx_dict[f'{attr_name}_uniqueidtype'] = attr_value.uniqueidtype
        
        return trx_dict

    def _extract_positions(self) -> List[Dict[str, Any]]:
        if not self._parsed:
            self.parse()

        positions = []
        statements = self.ofx_data.statements
        
        for statement in statements:
            if not hasattr(statement, 'positions') or statement.positions is None:
                continue
                
            account = statement.account
            account_info = {
                'account_id': getattr(account, 'acctid', ''),
                'broker_id': getattr(account, 'brokerid', ''),
            }
            
            for pos in statement.positions:
                pos_dict = self._position_to_dict(pos, account_info)
                positions.append(pos_dict)
        
        return positions

    def _position_to_dict(self, pos: Any, account_info: Dict[str, str]) -> Dict[str, Any]:
        pos_dict = {}
        pos_dict.update(account_info)
        
        for attr_name in dir(pos):
            if attr_name.startswith('_') or callable(getattr(pos, attr_name)):
                continue
                
            attr_value = getattr(pos, attr_name)
            
            if attr_value is None:
                continue
            
            if isinstance(attr_value, datetime):
                pos_dict[attr_name] = attr_value.isoformat()
            elif isinstance(attr_value, Decimal):
                pos_dict[attr_name] = float(attr_value)
            elif isinstance(attr_value, (str, int, float, bool)):
                pos_dict[attr_name] = attr_value
            elif hasattr(attr_value, '__dict__'):
                if hasattr(attr_value, 'uniqueid'):
                    pos_dict[f'{attr_name}_uniqueid'] = attr_value.uniqueid
                if hasattr(attr_value, 'uniqueidtype'):
                    pos_dict[f'{attr_name}_uniqueidtype'] = attr_value.uniqueidtype
        
        return pos_dict

    def to_csv(self, output_file: Optional[Union[str, Path]] = None) -> Path:
        if output_file is None:
            output_file = self.input_file.with_suffix('.csv')
        else:
            output_file = Path(output_file)

        transactions = self._extract_transactions()
        
        if not transactions:
            raise ValueError("No transactions found in OFX file")

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = set()
            for trx in transactions:
                fieldnames.update(trx.keys())
            fieldnames = sorted(fieldnames)
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(transactions)

        positions = self._extract_positions()
        if positions:
            positions_file = output_file.with_suffix('.positions.csv')
            with open(positions_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = set()
                for pos in positions:
                    fieldnames.update(pos.keys())
                fieldnames = sorted(fieldnames)
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(positions)

        return output_file

    def to_json(self, output_file: Optional[Union[str, Path]] = None, indent: int = 2) -> Path:
        if output_file is None:
            output_file = self.input_file.with_suffix('.json')
        else:
            output_file = Path(output_file)

        transactions = self._extract_transactions()
        
        if not transactions:
            raise ValueError("No transactions found in OFX file")

        data = {'transactions': transactions}
        
        positions = self._extract_positions()
        if positions:
            data['positions'] = positions

        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=indent if indent > 0 else None)

        return output_file


def convert_qfx(
    input_file: Union[str, Path],
    output_format: str = 'csv',
    output_file: Optional[Union[str, Path]] = None
) -> Path:
    converter = QFXConverter(input_file)
    
    if output_format.lower() == 'csv':
        return converter.to_csv(output_file)
    elif output_format.lower() == 'json':
        return converter.to_json(output_file)
    else:
        raise ValueError(f"Unsupported output format: {output_format}. Use 'csv' or 'json'.")
