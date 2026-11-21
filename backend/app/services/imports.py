import csv
import io
import zipfile
from xml.etree.ElementTree import ParseError
from openpyxl.utils.exceptions import InvalidFileException
from datetime import date, datetime
from pathlib import Path
from openpyxl import load_workbook
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from app.models.entities import SoilSample
from app.schemas.soil import SampleInput, PARAMETERS

MAX_ROWS = 5000
MAX_COLUMNS = 100


def parse_file(filename, content):
    suffix = Path(filename).suffix.lower()
    if suffix not in ['.csv', '.xlsx']:
        raise HTTPException(415, 'Only UTF-8 CSV and XLSX files are supported')
    try:
        if suffix == '.csv':
            text = content.decode('utf-8-sig')
            if '\x00' in text:
                raise ValueError('Binary content detected')
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t')
            reader = csv.reader(io.StringIO(text), dialect, strict=True)
        else:
            archive = zipfile.ZipFile(io.BytesIO(content))
            if sum(f.file_size for f in archive.infolist()) > 40 * 1024 * 1024 or len(archive.infolist()) > 500:
                raise ValueError('Workbook expands beyond the safe size limit')
            archive.close()
            workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=False, keep_links=False)
            if len(workbook.sheetnames) != 1:
                workbook.close()
                raise ValueError('Upload a workbook containing exactly one worksheet')
            reader = workbook.active.iter_rows(values_only=True)
        rows = []
        for index, row in enumerate(reader):
            if index > MAX_ROWS:
                raise ValueError(f'At most {MAX_ROWS} data rows are allowed')
            if len(row) > MAX_COLUMNS:
                raise ValueError('Too many columns')
            converted = [(v.isoformat()[:10] if isinstance(v, (date, datetime)) else str(v) if v is not None else '').strip() for v in row]
            if any(len(v) > 1000 for v in converted):
                raise ValueError('A cell exceeds 1000 characters')
            rows.append(converted)
        if suffix == '.xlsx':
            workbook.close()
        if len(rows) < 2:
            raise ValueError('A header row and at least one data row are required')
        headers = rows.pop(0)
        if any(not h for h in headers) or len(set(headers)) != len(headers):
            raise ValueError('Headers must be non-empty and unique')
        for row in rows:
            if len(row) != len(headers):
                raise ValueError('Every row must have the same number of cells as the header')
        return headers, [dict(zip(headers, row)) for row in rows]
    except (ValueError, UnicodeError, csv.Error, zipfile.BadZipFile, KeyError, OSError, ParseError, InvalidFileException) as error:
        raise HTTPException(422, f'Invalid file: {error}')


def validate_rows(db, item, specification):
    mapping = specification['columns']
    units, methods = specification.get('units', {}), specification.get('methods', {})
    allowed = {'sample_code', 'collected_on', 'field_id', 'location', 'laboratory'} | set(PARAMETERS) | {f'{p}_{suffix}' for p in PARAMETERS for suffix in ['unit','method']}
    if set(mapping) - allowed or len(set(mapping.values())) != len(mapping.values()):
        raise HTTPException(422, 'Mapping has unknown targets or maps a column more than once')
    headers = set(item.rows[0])
    if set(mapping.values()) - headers:
        raise HTTPException(422, 'Mapping refers to a column missing from the file')
    if not {'sample_code', 'collected_on'}.issubset(mapping):
        raise HTTPException(422, 'Map Sample ID and collection date')
    existing = set(db.scalars(select(SoilSample.sample_code).where(SoilSample.farm_id == item.farm_id)))
    valid, errors, seen = [], [], set()
    for row_number, row in enumerate(item.rows, 2):
        values = {target: row[source] for target, source in mapping.items()}
        code = values.get('sample_code', '')
        if code in seen or code in existing:
            errors.append((row_number, f'Duplicate Sample ID: {code}'))
            continue
        seen.add(code)
        try:
            measurements = []
            for p in PARAMETERS:
                if p in values:
                    if values[p] == '':
                        raise ValueError(f'{p}: missing value in a mapped parameter')
                    measurements.append({'parameter': p, 'value': values[p], 'unit': values.get(p+'_unit') or units.get(p, ''), 'method': values.get(p+'_method') or methods.get(p, '')})
            sample = SampleInput(farm_id=item.farm_id, field_id=values.get('field_id') or None, sample_code=code, collected_on=values.get('collected_on',''), location=values.get('location',''), laboratory=values.get('laboratory',''), measurements=measurements)
            if sample.field_id:
                from app.models.entities import Field
                field = db.get(Field, sample.field_id)
                if not field or field.farm_id != item.farm_id:
                    raise ValueError('Field must belong to the selected farm')
            valid.append(sample.model_dump(mode='json'))
        except (ValidationError, ValueError) as error:
            errors.append((row_number, str(error)))
    return valid, errors


def safe_csv(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value
