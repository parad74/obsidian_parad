"""HTTP and startup checks on temporary SQLite files; the user database is read-only."""
from pathlib import Path
from contextlib import contextmanager, closing
import base64
import hmac
import http.cookiejar
import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

vault = Path(__file__).resolve().parents[3]
project = vault / 'Sources/Book4U'
source_db = project / 'Book4U.Model.Sqlite.CodeFirst.ExportImport/book4u.db'
api_dll = project / 'WebAPI.Book4U.Model.Sqlite.CodeFirst/bin/Debug/netcoreapp3.1/win-x64/WebAPI.Book4U.Model.Sqlite.CodeFirst.dll'
report_path = Path(__file__).with_name('webapi-verification.json')
source_hash = hashlib.sha256(source_db.read_bytes()).hexdigest()
source_uri = source_db.as_uri() + '?mode=ro'
with closing(sqlite3.connect(source_uri, uri=True)) as source, source:
    schema = dict(source.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('Room','CommandResult')"))
assert set(schema) == {'Room', 'CommandResult'}, 'Both table definitions are required'
workspace = Path(tempfile.mkdtemp(prefix='book4u-webapi-')).resolve()
assert workspace.parent == Path(tempfile.gettempdir()).resolve()
database = workspace / 'book4u.db'
with closing(sqlite3.connect(database)) as db, db:
    for sql in schema.values():
        db.execute(sql)
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
base = f'http://127.0.0.1:{port}'
host_environment = dict(os.environ, ASPNETCORE_ENVIRONMENT='Production', DOTNET_ENVIRONMENT='Production')
checks = []
process = None
log_file = workspace / 'host.log'

def request(method, path, data=None, expected=200, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode('utf-8') if data is not None else None
    req = urllib.request.Request(base + path, data=body, method=method,
                                 headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as response_error:
        response = response_error
    with response:
        status = response.status
        raw = response.read().decode('utf-8')
        content_type = response.headers.get_content_type()
    assert status == expected, f'{method} {path}: {status}, expected {expected}: {raw[:1200]}'
    if status == 200 and path in ('/api/book4uwebapi/ping', '/api/book4uwebapi/pingsecure'):
        assert content_type == 'application/json', content_type
        assert raw == '"Pong"', raw
    return json.loads(raw) if raw else None

def by_code(route, code):
    return f'/api/{route}/by-code?' + urllib.parse.urlencode({'code': code})

def read_by_code(route, code, expected=200):
    return request('POST', f'/api/{route}/by-code', {'code': code}, expected)


def rows(table):
    with closing(sqlite3.connect(database)) as db, db:
        return db.execute(f'SELECT ID, Code, Tag FROM "{table}" ORDER BY ID').fetchall()

def startup_failure(folder, extra, expected_text):
    result = subprocess.run(['dotnet', str(api_dll), '--urls', base] + extra,
                            cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
                            creationflags=subprocess.CREATE_NO_WINDOW, env=host_environment)
    output = result.stdout + result.stderr
    assert result.returncode == 1 and expected_text in output, output[-1600:]
    assert 'WebAPI stopped:' in result.stderr, result.stderr
    assert 'Exception' in result.stderr and 'Program.Main' in result.stderr, result.stderr


def token(key, **changes):
    payload = {'iss': 'book4u-test', 'aud': 'book4u-tests', 'sub': 'test-reader',
               'exp': int(time.time()) + 300}
    payload.update(changes)
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).rstrip(b'=')
    body = encode({'alg': 'HS256', 'typ': 'JWT'}) + b'.' + encode(payload)
    signature = base64.urlsafe_b64encode(hmac.new(key.encode(), body, hashlib.sha256).digest()).rstrip(b'=')
    return (body + b'.' + signature).decode()


def expanded_http_checks():
    document = request('GET', '/swagger/v1/swagger.json')
    assert document['info']['title'] == 'WebAPI.Book4U.Model.Sqlite.CodeFirst'
    for path in ['/api/rooms/batch', '/api/command-results/selection', '/api/test/ado', '/api/rooms/ado', '/api/command-results/ado', '/api/book4uwebapi/pingsecure']:
        assert path in document['paths'], path
    summary = document['paths']['/api/rooms/page']['post']['summary']
    assert 'полным количеством' in summary, summary
    assert any(name.startswith('Book4U.Model.') for name in document['components']['schemas'])
    with urllib.request.urlopen(base + '/swagger/index.html') as response:
        assert b'Swagger UI' in response.read()
    for path in ['/api/rooms/page', '/api/rooms/by-code', '/api/command-results/page', '/api/command-results/by-code',
                 '/api/command-results/by-parent-code', '/api/command-results/by-command-result-code', '/api/test/filters']:
        operation = document['paths'][path]['post']
        assert 'requestBody' in operation, path
        assert not any(parameter['in'] == 'query' for parameter in operation.get('parameters', [])), path
        assert 'get' not in document['paths'][path], path
    by_id = document['paths']['/api/rooms/by-id/{id}']['put']
    assert any(parameter['name'] == 'id' and parameter['in'] == 'path' for parameter in by_id['parameters'])
    checks.append('Parameterized reads use POST with JSON bodies; query-only input fails; PUT by-id retains ID in the route')
    checks.append('Swagger JSON/UI, XML action summaries, fully qualified schema names and expanded routes')
    for path in ['/api/book4uwebapi/ping', '/api/book4uwebapi/pingsecure']:
        content = document['paths'][path]['get']['responses']['200']['content']
        assert set(content) == {'application/json'}, content
        assert content['application/json']['schema']['type'] == 'string', content
    checks.append('Original Ping contract: HTTP 200, application/json, exact JSON string Pong, common response and service-specific routes')
    config = request('GET', '/api/test/configuration')
    assert config['sameOptionsInstance'] and config['sameLocatorInstance'], config
    assert config['validatedSettings'] == 4 and config['primary'] == 'Book4U' and config['secondary'] == 'SQLite', config
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for visit in (1, 2):
        req = urllib.request.Request(base + '/api/test/session', data=b'', method='POST')
        with opener.open(req) as response:
            assert json.load(response)['visits'] == visit
    result = request('POST', '/api/test/filters', '  example  ')
    assert result == {'text': 'example'}, result
    request('POST', '/api/rooms/page', {'sortBy': 'code'})
    request('POST', '/api/test/notifications', {'message': 'local-test'}, 503)
    assert request('POST', '/api/test/command-hub', {'message': 'local-test'}) == {'sent': False}
    request('POST', '/api/test/command-hub', {}, 400)
    request('GET', '/api/book4uwebapi/pingsecure', expected=401)
    request('POST', '/hubs/book4u/negotiate', expected=404)
    error = request('GET', '/missing-route', expected=404)
    assert error['status'] == 404 and 'traceId' in error
    req = urllib.request.Request(base + '/api/rooms', method='OPTIONS', headers={
        'Origin': 'https://client.example', 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type,authorization'})
    with urllib.request.urlopen(req) as response:
        assert response.status == 204 and response.headers['Access-Control-Allow-Origin'] == '*'
    forged = token('temporary-test-signing-key-no-real-secrets')
    decoded = request('GET', '/api/claims/decoded', headers={'Authorization': 'Bearer ' + forged})
    assert decoded['validated'] is False and any(item['value'] == 'test-reader' for item in decoded['claims'])
    request('GET', '/api/claims', expected=401, headers={'Authorization': 'Bearer ' + forged})
    checks.append('Unity named registrations, four shared validated options, ServiceLocator bridge, session cookie, both action filters, CORS, errors, JWT/SignalR disabled defaults')
    for route in ['rooms', 'command-results']:
        prefix = '/api/' + route
        request('POST', prefix + '/batch', [None], 400)
        request('POST', prefix + '/batch', [
            {'code': 'batch-code', 'tag': 'batch-first', 'sessionCode': 'session-a', 'parentCommandResultCode': 'parent-test', 'commandResultCode': 'result-a'},
            {'code': 'batch-code', 'tag': 'batch-second', 'sessionCode': 'session-b', 'parentCommandResultCode': 'parent-test', 'commandResultCode': 'result-b'}], 204)
        by_list = {'filterStringListParams': {'Code': {'values': ['batch-code']}}}
        result = request('POST', prefix + '/selection', by_list)
        assert result['totalCount'] == 2
        ids = [item['id'] for item in result['items']]
        request('PUT', prefix, {'code': 'batch-code', 'tag': 'updated-by-body', 'id': 999999}, 204)
        assert read_by_code(route, 'batch-code')['id'] == ids[0]
        assert read_by_code(route, 'batch-code')['tag'] == 'updated-by-body'
        by_ids = request('POST', prefix + '/selection', {'filterListParams': {'ID': {'values': ids}}})
        assert by_ids['totalCount'] == 2
        page = request('POST', prefix + '/selection', {**by_list, 'isEnablePaging': True,
                       'currentPage': 1, 'countOfRecordsOnPage': 1, 'sortParams': 'ID DESC'})
        assert len(page['items']) == 1 and page['totalCount'] == 2 and page['items'][0]['id'] == ids[1]
        # Ready SelectParams retains library semantics instead of the page adapter's rules.
        selected = request('POST', prefix + '/selection', {'filterParams': {'Code': {'operator': 2, 'value': 'batch-code'}}})
        assert selected['totalCount'] == 2
        contains = request('POST', prefix + '/selection', {'filterParams': {'Code': {'operator': 7, 'value': 'batch-'}}})
        assert contains['totalCount'] == 2
        literal_all = request('POST', prefix + '/selection', {'filterStringListParams': {'Code': {'values': ['[All]']}}})
        assert literal_all['totalCount'] == 1 and literal_all['items'][0]['code'] == '[All]'
        full = request('GET', prefix + '/all')
        # Existing SelectParam removes [All] from FilterParams then parses an empty expression.
        request('POST', prefix + '/selection', {'filterParams': {'Code': {'operator': 2, 'value': '[All]'}}}, 500)
        for unchanged in [
                {'filterStringListParams': {'Code': {'values': []}}},
                {'filterTemplate': 'unused', 'extra': {'clientNote': 'preserved'}}]:
            selected = request('POST', prefix + '/selection', unchanged)
            assert selected['totalCount'] == full['totalCount'], selected
        request('POST', prefix + '/selection', expected=400)
        request('DELETE', prefix + '/all', expected=404)
        all_items = request('GET', prefix + '/all')
        assert all_items['totalCount'] == len(all_items['items'])
    # Re-insert separate records: Update(body) replaces all data of the first matching record.
    prefix = '/api/command-results'
    inserted = request('POST', prefix, {'code': 'details', 'commandResultCode': 'details-result',
                        'parentCommandResultCode': 'details-parent', 'sessionCode': 'details-session',
                        'startDateTime': '2026-10-08T10:30:00', 'sumQuantityEdit': 1.25, 'step': 2}, 200)
    assert request('GET', prefix + f'/by-id/{inserted}')['code'] == 'details'
    request('GET', prefix + '/by-id/999999', expected=404)
    assert request('POST', prefix + '/by-parent-code', {'code': 'details-parent'})['totalCount'] == 1
    assert request('POST', prefix + '/by-command-result-code', {'code': 'details-result'})['id'] == inserted
    assert request('POST', prefix + '/selection-test', {'sessionCodes': ['details-session']})['totalCount'] == 1
    assert request('POST', prefix + '/selection-test', {'contains': 'details-'})['totalCount'] == 1
    for field, value in [('SumQuantityEdit', 1.25), ('Step', 2)]:
        match = request('POST', prefix + '/selection', {'filterParams': {field: {'operator': 2, 'value': value}}})
        assert any(item['id'] == inserted for item in match['items']), match
    date_match = request('POST', prefix + '/selection', {'filterDateTimeParams': {
        'StartDateTime': {'operator': 12, 'value': '2026-10-08T00:00:00', 'value1': '2026-10-08T00:00:00'}}})
    assert any(item['id'] == inserted for item in date_match['items'])
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    assert request('GET', prefix + '/test-data')['totalCount'] > 0
    assert isinstance(request('GET', '/api/test/ado'), list)
    expected_codes = [row[1] for row in rows('CommandResult')]
    assert expected_codes.count('batch-code') == 2
    assert request('GET', '/api/command-results/ado') == expected_codes
    expected_room_codes = [row[1] for row in rows('Room')]
    assert expected_room_codes.count('batch-code') == 2
    assert request('GET', '/api/rooms/ado') == expected_room_codes
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    checks.append('Expanded repository operations: batch/all, body-Code update, ID/parent/result reads, direct SelectParams: lists, filters, paging, reserved marker and ignored metadata, session filter examples, in-memory samples and Room, CommandResult and diagnostic read-only SQLite ADO actions (ordered codes, duplicates, empty table)')

try:
    with log_file.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(['dotnet', str(api_dll), '--urls', base, '--WebApi:EnableDiagnostics', 'true'], cwd=workspace,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW, env=host_environment)
        for attempt in range(80):
            if process.poll() is not None:
                raise AssertionError('Host exited:\n' + log_file.read_text(encoding='utf-8'))
            try:
                request('GET', '/api/book4uwebapi/ping')
                break
            except urllib.error.URLError:
                time.sleep(0.25)
        else:
            raise AssertionError('Host did not become ready')
        checks.append('Host starts with Unity and resolves both repository/controller graphs')
        for route, table in [('rooms', 'Room'), ('command-results', 'CommandResult')]:
            prefix = '/api/' + route
            empty = request('POST', prefix + '/page', {})
            assert empty == {'items': [], 'totalCount': 0}, empty
            request('POST', prefix + '/by-code', expected=400)
            read_by_code(route, 'missing', expected=404)
            for selection in [{'page': 0}, {'pageSize': 101}, {'sortBy': 'NotAColumn'}, {'page': 2147483647, 'pageSize': 100}]:
                request('POST', prefix + '/page', selection, expected=400)
            request('POST', prefix + '/page', expected=400)
            request('POST', prefix + '/page?page=1&pageSize=20', expected=400)
            request('POST', prefix + '/by-code?code=missing', expected=400)
            request('POST', prefix + '/by-code', {}, expected=400)
            request('POST', prefix + '/page', {'page': 'not-a-number'}, expected=400)
            request('GET', prefix, expected=405)
            request('GET', prefix + '/by-code?code=missing', expected=405)
            first = request('POST', prefix, {'id': 999999, 'code': 'shared', 'tag': 'first'}, 200)
            second = request('POST', prefix, {'code': 'shared', 'tag': 'second'}, 200)
            assert first != 999999 and second != first
            page = request('POST', prefix + '/page', {'pageSize': 1, 'sortBy': 'Code'})
            assert len(page['items']) == 1 and page['totalCount'] == 2, page
            filtered = request('POST', prefix + '/page', {'code': 'shared'})
            assert len(filtered['items']) == 2 and filtered['totalCount'] == 2
            assert request('POST', prefix + '/page?code=ignored', {'code': 'shared'}) == filtered
            assert read_by_code(route, 'shared')['id'] == first
            request('PUT', prefix + f'/by-id/{first}',
                    {'id': second, 'code': 'moved', 'tag': 'id-updated'}, 204)
            assert rows(table) == [(first, 'moved', 'id-updated'), (second, 'shared', 'second')]
            request('PUT', by_code(route, 'shared'),
                    {'id': first, 'code': 'renamed', 'tag': 'code-updated'}, 204)
            assert rows(table) == [(first, 'moved', 'id-updated'), (second, 'renamed', 'code-updated')]
            request('PUT', prefix + '/by-id/999999', {'code': 'not-found'}, 204)
            request('PUT', by_code(route, 'not-found'), {'code': 'not-found'}, 204)
            for code in ['renamed', 'renamed', '', '[All]', 'x" || true || Code == "x', 'back\\slash']:
                request('POST', prefix, {'code': code, 'tag': 'literal'}, 200)
            for code in ['', '[All]', 'x" || true || Code == "x', 'back\\slash']:
                result = request('POST', prefix + '/page', {'code': code})
                assert result['totalCount'] == 1 and result['items'][0]['code'] == code, result
                read_by_code(route, code)
            request('DELETE', by_code(route, 'renamed'), expected=204)
            assert all(row[1] != 'renamed' for row in rows(table))
            request('DELETE', by_code(route, 'not-found'), expected=204)
            with closing(sqlite3.connect(database)) as db, db:
                db.execute(f"CREATE TRIGGER fail_update BEFORE UPDATE ON \"{table}\" BEGIN SELECT RAISE(ABORT, 'internal-test-only'); END;")
            error = request('PUT', prefix + f'/by-id/{first}', {'code': 'must-not-change'}, 500)
            assert error['status'] == 500 and 'internal-test-only' not in json.dumps(error)
            assert rows(table)[0][1] == 'moved'
            with closing(sqlite3.connect(database)) as db, db:
                db.execute('DROP TRIGGER fail_update')
            request('POST', prefix + '/page', {})
            print(route + ': HTTP checks passed', flush=True)
            checks.append(route + ': collection/count, validation, generated ID, duplicate Code, both updates, literal filters, delete-all-by-Code, async error and recovery')
        expanded_http_checks()
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        process.wait(timeout=15)
    after = hashlib.sha256(source_db.read_bytes()).hexdigest()
    assert after == source_hash, 'Source database changed'

@contextmanager
def running_host(folder, extra=None):
    startup_log = folder / 'startup.log'
    with startup_log.open('w', encoding='utf-8') as log:
        child = subprocess.Popen(['dotnet', str(api_dll), '--urls', base] + (extra or []), cwd=folder,
                                 stdout=log, stderr=subprocess.STDOUT,
                                 creationflags=subprocess.CREATE_NO_WINDOW, env=host_environment)
        try:
            for attempt in range(80):
                if child.poll() is not None:
                    raise AssertionError(startup_log.read_text(encoding='utf-8'))
                try:
                    request('GET', '/api/book4uwebapi/ping')
                    break
                except urllib.error.URLError:
                    time.sleep(0.25)
            else:
                raise AssertionError('Host did not become ready')
            yield
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=15)


def verify_empty_migrated_database(path):
    expected_tables = {'Author', 'Book', 'Category', 'Location', 'Room', 'CommandResult'}
    with closing(sqlite3.connect(path)) as db, db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert expected_tables <= tables, tables
        migrations = [row[0] for row in db.execute('SELECT MigrationId FROM __EFMigrationsHistory ORDER BY MigrationId')]
        assert migrations == ['20261002181021_InitialCreate', '20261003113005_AddBookDataModel'], migrations
        for table in expected_tables:
            assert db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0, table


missing_folder = workspace / 'missing'
missing_folder.mkdir()
created_database = missing_folder / 'book4u.db'
assert not created_database.exists()
with running_host(missing_folder):
    verify_empty_migrated_database(created_database)
    assert request('GET', '/api/command-results/ado') == []
    assert request('GET', '/api/rooms/ado') == []
    saved_id = request('POST', '/api/rooms', {'code': 'startup-retained', 'tag': 'preserved'}, 200)
checks.append('Missing DB: host applies both prepared migrations, creates all six model tables without seed, and serves HTTP')
existing_hash = hashlib.sha256(created_database.read_bytes()).hexdigest()
with running_host(missing_folder):
    saved = read_by_code('rooms', 'startup-retained')
    assert saved['id'] == saved_id and saved['tag'] == 'preserved'
assert hashlib.sha256(created_database.read_bytes()).hexdigest() == existing_hash
checks.append('Restart with existing DB: user row, ID and full database SHA-256 unchanged')
assert created_database.parent.parent == workspace
created_database.unlink()
with running_host(missing_folder):
    verify_empty_migrated_database(created_database)
    assert request('GET', '/api/command-results/ado') == []
    assert request('GET', '/api/rooms/ado') == []
    read_by_code('rooms', 'startup-retained', expected=404)
checks.append('After deleting only the temporary DB file, restart recreates an empty migrated database')
with closing(sqlite3.connect(database)) as db, db:
    assert db.execute("SELECT name FROM sqlite_master WHERE name='__EFMigrationsHistory'").fetchone() is None
checks.append('Existing two-table fixture left without migration history or extra tables: startup does not migrate an existing file')
startup_failure(workspace, ['--WebApi:MaxPageSize', '0'], 'MaxPageSize')
blocked_folder = workspace / 'blocked'
blocked_folder.mkdir()
(blocked_folder / 'book4u.db').mkdir()
startup_failure(blocked_folder, [], 'WebAPI stopped:')
checks.append('Invalid typed options or failure to create the database stops the host with a nonzero exit code')

# These settings are process arguments only, never written to application configuration.
for extra, message in [
    (['--Book4USettings:AppDataPath', ''], 'AppDataPath'),
    (['--Jwt:Enabled', 'true'], 'Jwt:'),
    (['--SignalR:ClientsEnabled', 'true'], 'SignalR:')]:
    startup_failure(workspace, extra, message)
checks.append('Each IValidatable participates: invalid Book4U paths, JWT and SignalR settings reject startup')
with running_host(workspace):
    request('GET', '/api/test/configuration', expected=404)
    request('DELETE', '/api/rooms/all', expected=404)
    request('GET', '/api/book4uwebapi/pingsecure', expected=401)
checks.append('Production/default profile disables diagnostics and maintenance; protected Ping remains 401')
key = base64.urlsafe_b64encode(os.urandom(36)).decode()
with running_host(workspace, ['--Jwt:Enabled', 'true', '--Jwt:Issuer', 'book4u-test', '--Jwt:Audience', 'book4u-tests',
                              '--Jwt:SigningKey', key, '--WebApi:EnableDiagnostics', 'true']):
    auth = {'Authorization': 'Bearer ' + token(key)}
    assert request('GET', '/api/book4uwebapi/pingsecure', headers=auth) == 'Pong'
    assert request('GET', '/api/claims', headers=auth)['validated']
    for bad in [token(key + 'wrong'), token(key, aud='wrong'), token(key, iss='wrong'), token(key, exp=int(time.time()) - 120)]:
        request('GET', '/api/book4uwebapi/pingsecure', expected=401, headers={'Authorization': 'Bearer ' + bad})
checks.append('Opt-in JWT: valid local signature succeeds; wrong signature/issuer/audience and expired tokens fail')
with running_host(workspace, ['--SignalR:ServerEnabled', 'true', '--WebApi:EnableDiagnostics', 'true']):
    negotiated = request('POST', '/hubs/book4u/negotiate?negotiateVersion=1')
    connection_id = negotiated.get('connectionToken', negotiated['connectionId'])
    hub_url = base + '/hubs/book4u?' + urllib.parse.urlencode({'id': connection_id})
    # SignalR LongPolling protocol: open transport, JSON handshake, then receive a notification.
    with urllib.request.urlopen(hub_url, timeout=10) as response:
        response.read()
    handshake = urllib.request.Request(hub_url, data=b'{"protocol":"json","version":1}\x1e',
                                       method='POST', headers={'Content-Type': 'text/plain'})
    with urllib.request.urlopen(handshake, timeout=10) as response:
        response.read()
    with urllib.request.urlopen(hub_url, timeout=10) as response:
        handshake_reply = response.read()
    assert b'{}' in handshake_reply, handshake_reply
    request('POST', '/api/test/notifications', {'message': 'test-notification'}, 202)
    with urllib.request.urlopen(hub_url, timeout=10) as response:
        notification = response.read()
    assert b'Notification' in notification and b'test-notification' in notification, notification
    with urllib.request.urlopen(urllib.request.Request(hub_url, method='DELETE'), timeout=10) as response:
        response.read()
checks.append('Opt-in local SignalR server: negotiate/handshake and real queued HostedService notification delivered via LongPolling')
with running_host(workspace, ['--WebApi:EnableMaintenance', 'true']):
    for route in ['rooms', 'command-results']:
        request('DELETE', '/api/' + route + '/all', expected=204)
        assert request('GET', '/api/' + route + '/all')['totalCount'] == 0
checks.append('Explicit maintenance option allows DeleteAll on temporary data only')
assert 'Invalid model for' in log_file.read_text(encoding='utf-8'), 'Automatic bad-request logging did not run'
checks.append('Invalid model logs a bad request before the controller action')

# Check the independent publish artifact, not just the Debug output.
publish_folder = project / 'WebAPI.Book4U.Model.Sqlite.CodeFirst/bin/Release/netcoreapp3.1/win-x64/publish'
for name in ['WebAPI.Book4U.Model.Sqlite.CodeFirst.exe', 'WebAPI.Book4U.Model.Sqlite.CodeFirst.dll',
             'WebAPI.Book4U.Model.Sqlite.CodeFirst.xml', 'appsettings.json', 'appsettings.Development.json',
             'appsettings.Production.json', 'install.bat', 'uninstall.bat']:
    assert (publish_folder / name).is_file(), name
saved_api_dll = api_dll
api_dll = publish_folder / 'WebAPI.Book4U.Model.Sqlite.CodeFirst.dll'
published_workspace = workspace / 'published'
published_workspace.mkdir()
try:
    with running_host(published_workspace):
        request('GET', '/api/book4uwebapi/ping')
        request('GET', '/swagger/v1/swagger.json')
        verify_empty_migrated_database(published_workspace / 'book4u.db')
        assert request('GET', '/api/command-results/ado') == []
        assert request('GET', '/api/rooms/ado') == []
finally:
    api_dll = saved_api_dll
checks.append('Published win-x64 artifact includes EXE/XML/settings/service scripts and runs with Swagger and fresh migrated DB; no Windows service installed')
assert hashlib.sha256(source_db.read_bytes()).hexdigest() == source_hash
checks.append('User database SHA-256 unchanged; migrations applied only to newly created temporary database files')
report = {'result': 'passed', 'knownLimitations': ['Known library defect reproduced: a sole FilterParams Code Equal [All] produces an empty expression and HTTP 500; literal [All] through FilterStringListParams succeeds.'], 'checks': checks, 'sourceDatabaseSha256': source_hash,
          'temporaryWorkspace': str(workspace), 'hostLog': str(log_file)}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
