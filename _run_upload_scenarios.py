import os, json, requests, time
URL = 'http://127.0.0.1:5000/upload'
PDF_PATH = r'samples/Naukri_MayurPatil[3y_2m].pdf'
JD_TEXT = 'Need a Python backend engineer with Django and API experience'


def to_bool_intelligence(payload):
    if not isinstance(payload, dict):
        return False
    if 'has_intelligence_data' in payload:
        return bool(payload.get('has_intelligence_data'))
    intel = payload.get('intelligence')
    return bool(intel)


def contains_intelligence(payload):
    if not isinstance(payload, dict):
        return False
    if 'contains_intelligence' in payload:
        return bool(payload.get('contains_intelligence'))
    return 'intelligence' in payload and bool(payload.get('intelligence'))


def run_scenario(name, data, expected_pipeline):
    rows = []
    for i in range(1, 16):
        rec = {'scenario': name, 'index': i}
        try:
            with open(PDF_PATH, 'rb') as f:
                files = {'cv_file': (os.path.basename(PDF_PATH), f, 'application/pdf')}
                r = requests.post(URL, data=data, files=files, timeout=300)
            rec['status_code'] = r.status_code
            try:
                j = r.json()
            except Exception:
                j = None
                rec['pipeline_executed'] = None
                rec['contains_intelligence'] = False
                rec['has_intelligence_data'] = False
                rec['error'] = f'non-json: {r.text[:160]}'
            else:
                rec['pipeline_executed'] = j.get('pipeline_executed')
                rec['contains_intelligence'] = contains_intelligence(j)
                rec['has_intelligence_data'] = to_bool_intelligence(j)
                rec['error'] = j.get('error')
        except Exception as e:
            rec['status_code'] = None
            rec['pipeline_executed'] = None
            rec['contains_intelligence'] = False
            rec['has_intelligence_data'] = False
            rec['error'] = str(e)
        rows.append(rec)

    mismatch = []
    for rec in rows:
        if rec['status_code'] != 200:
            mismatch.append(f"#{rec['index']} status={rec['status_code']}")
            continue
        if rec['error']:
            mismatch.append(f"#{rec['index']} error={rec['error']}")
        if expected_pipeline == 'redaction_only' and rec['pipeline_executed'] == 'full':
            mismatch.append(f"#{rec['index']} no-JD returned full")
        if expected_pipeline == 'full' and rec['pipeline_executed'] != 'full':
            mismatch.append(f"#{rec['index']} with-JD not full (pipeline={rec['pipeline_executed']})")
        if expected_pipeline == 'redaction_only' and rec['has_intelligence_data']:
            mismatch.append(f"#{rec['index']} no-JD has intelligence data")
        if expected_pipeline == 'full' and not rec['has_intelligence_data']:
            mismatch.append(f"#{rec['index']} with-JD missing intelligence data")

    summary = {
        'total': len(rows),
        'status_200': sum(1 for r in rows if r['status_code'] == 200),
        'status_non_200': sum(1 for r in rows if r['status_code'] != 200),
        'pipeline_full': sum(1 for r in rows if r['pipeline_executed'] == 'full'),
        'pipeline_redaction_only': sum(1 for r in rows if r['pipeline_executed'] == 'redaction_only'),
        'contains_intelligence_true': sum(1 for r in rows if r['contains_intelligence']),
        'has_intelligence_data_true': sum(1 for r in rows if r['has_intelligence_data']),
        'error_count': sum(1 for r in rows if r['error']),
        'mismatch_count': len(mismatch)
    }
    return rows, summary, mismatch

no_jd_rows, no_jd_summary, no_jd_mismatch = run_scenario('no_jd', {}, 'redaction_only')
with_jd_rows, with_jd_summary, with_jd_mismatch = run_scenario('with_jd', {'job_description': JD_TEXT}, 'full')

result = {
    'no_jd': {'summary': no_jd_summary, 'mismatches': no_jd_mismatch, 'rows': no_jd_rows},
    'with_jd': {'summary': with_jd_summary, 'mismatches': with_jd_mismatch, 'rows': with_jd_rows}
}
with open('upload_scenario_results.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print('NO_JD_SUMMARY', json.dumps(no_jd_summary, separators=(',', ':')))
print('WITH_JD_SUMMARY', json.dumps(with_jd_summary, separators=(',', ':')))
if no_jd_mismatch:
    print('NO_JD_MISMATCHES', '; '.join(no_jd_mismatch))
else:
    print('NO_JD_MISMATCHES none')
if with_jd_mismatch:
    print('WITH_JD_MISMATCHES', '; '.join(with_jd_mismatch))
else:
    print('WITH_JD_MISMATCHES none')
