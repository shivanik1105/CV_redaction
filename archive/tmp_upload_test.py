from pathlib import Path
import traceback
import sys

try:
    import app as app_module

    flask_app = getattr(app_module, 'app', None)
    if flask_app is None and hasattr(app_module, 'create_app'):
        flask_app = app_module.create_app()
    if flask_app is None:
        raise RuntimeError('No Flask app instance found in app.py')

    sample_path = Path('samples/Resume -Sunil Durgale.pdf')
    if not sample_path.exists():
        raise FileNotFoundError(f'Sample file not found: {sample_path}')

    with flask_app.test_client() as client:
        with sample_path.open('rb') as f:
            data = {
                'cv_file': (f, sample_path.name),
                'llm_provider': 'openai',
                'llm_model': 'gpt-4o-mini',
                'llm_api_key': 'runtime_test_key',
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')

    print(f'STATUS_CODE: {response.status_code}')
    print('RESPONSE_BODY_BEGIN')
    print(response.get_data(as_text=True))
    print('RESPONSE_BODY_END')

except Exception as exc:
    print('TRACEBACK_BEGIN')
    print(traceback.format_exc())
    print('TRACEBACK_END')

    etype, eval_, etb = sys.exc_info()
    stack = traceback.extract_tb(etb) if etb else []
    print('KEY_STACK_LINES_BEGIN')
    for frame in stack[-8:]:
        print(f'File "{frame.filename}", line {frame.lineno}, in {frame.name}: {frame.line}')
    print('KEY_STACK_LINES_END')

    root = exc
    while getattr(root, '__cause__', None) is not None:
        root = root.__cause__
    print(f'ROOT_CAUSE: {type(root).__name__}: {root}')
