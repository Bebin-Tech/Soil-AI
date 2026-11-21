import importlib.util
import json
from pathlib import Path

path=Path(__file__).resolve().parents[2]/'machine_learning/preprocessing/audit.py'
spec=importlib.util.spec_from_file_location('dataset_audit',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_audit_refuses_unknown_units_and_crop_labels_as_fertility(tmp_path):
    data=tmp_path/'data.csv';data.write_text('nitrogen,label,site\n10,rice,A\n10,rice,A\n',encoding='utf-8')
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'name':'TEST FIXTURE ONLY','version':'1','source_url':'https://example.org','licence':'test fixture','collection_region':'test','collection_method':'test fixture','task':'fertility','target':'label','target_definition':'invalid crop target','features':{'nitrogen':{'unit':'unknown','method':'unknown'}},'group_column':'site','regional_validation':{'status':'unverified'}}),encoding='utf-8')
    result=module.audit_dataset(data,manifest)
    assert result['eligible_for_training'] is False
    assert result['duplicate_rows']==1
    assert any('not crop names' in b for b in result['blockers'])
    assert any('verified unit' in b for b in result['blockers'])
