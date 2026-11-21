"""Deterministic dataset audit. No targets, units or accuracy scores are invented."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def audit_dataset(csv_path,manifest_path):
    csv_path,manifest_path=Path(csv_path),Path(manifest_path)
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    required=['name','version','source_url','licence','collection_region','collection_method','target','target_definition','features','group_column','regional_validation']
    blockers=[f'Missing provenance: {key}' for key in required if not manifest.get(key)]
    if not str(manifest.get('source_url','')).startswith('https://'):
        blockers.append('Source URL must be an HTTPS origin record')
    features=manifest.get('features',{})
    for name,definition in features.items():
        for field in ['unit','method']:
            if not definition.get(field) or definition[field].lower() in ['unknown','unspecified','ratio']:
                blockers.append(f'{name}: verified {field} is required')
    with csv_path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        headers=reader.fieldnames or []
        if len(set(headers))!=len(headers):blockers.append('Duplicate column headers')
        rows=list(reader)
    target=manifest.get('target')
    if target in features:blockers.append('Target leakage: target is included in features')
    expected=set(features)|{target,manifest.get('group_column')}
    if expected-set(headers):blockers.append('Missing columns: '+', '.join(sorted(str(k) for k in expected-set(headers))))
    missing={key:sum(not row.get(key,'').strip() for row in rows) for key in headers}
    fingerprints=Counter(tuple(row.get(key,'') for key in headers) for row in rows)
    duplicates=sum(count-1 for count in fingerprints.values())
    if duplicates:blockers.append(f'{duplicates} duplicate rows; remove with a recorded policy before splitting')
    if any(missing.values()):blockers.append('Missing values require a documented policy; targets/groups cannot be imputed')
    summary,invalid,outliers={},[],{}
    for feature,definition in features.items():
        values=[]
        for index,row in enumerate(rows,2):
            try:
                value=float(row.get(feature,''))
                if not math.isfinite(value):raise ValueError()
                if definition.get('min') is not None and value<definition['min']:raise ValueError()
                if definition.get('max') is not None and value>definition['max']:raise ValueError()
                values.append(value)
            except ValueError:invalid.append({'row':index,'column':feature})
        if values:
            summary[feature]={'count':len(values),'min':min(values),'max':max(values),'mean':statistics.mean(values),'median':statistics.median(values),'unit':definition.get('unit'),'method':definition.get('method')}
            if len(values)>=4:
                q1,_,q3=statistics.quantiles(values,n=4)
                iqr=q3-q1
                outliers[feature]=sum(value<q1-1.5*iqr or value>q3+1.5*iqr for value in values)
    if invalid:blockers.append(f'{len(invalid)} invalid numeric values')
    balance=dict(Counter(row.get(target,'') for row in rows)) if target else {}
    if len(balance)<2:blockers.append('Classification requires at least two independently defined target classes')
    if balance and min(balance.values())<10:blockers.append('Every class requires at least 10 observations for the configured evaluation')
    if manifest.get('task')=='fertility' and set(balance)-{'low','medium','high'}:
        blockers.append('Fertility labels must be independently verified low/medium/high classes, not crop names')
    groups=Counter(row.get(manifest.get('group_column'), '') for row in rows)
    if len(groups)<5:blockers.append('At least five independent collection groups are required for grouped evaluation')
    if not manifest.get('target_reviewed_by') or not manifest.get('target_reference_url'):
        blockers.append('Target definition needs an agronomic reviewer and source reference')
    if manifest.get('regional_validation',{}).get('status')!='verified':
        blockers.append('Regional validation is not verified; production model activation is prohibited')
    return {'name':manifest.get('name'),'version':manifest.get('version'),'sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest(),'rows':len(rows),'columns':headers,'missing':missing,'duplicate_rows':duplicates,'invalid_values':invalid,'class_balance':balance,'independent_groups':len(groups),'summary':summary,'iqr_outlier_counts':outliers,'blockers':blockers,'eligible_for_training':not blockers,'policy':'No automatic unit conversion, target derivation, outlier removal, or model activation.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv',required=True,type=Path);parser.add_argument('--manifest',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=audit_dataset(args.csv,args.manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"Audited {report['rows']} rows; {len(report['blockers'])} blockers. Report: {args.output}")
    return 0 if report['eligible_for_training'] else 2


if __name__=='__main__':raise SystemExit(main())
