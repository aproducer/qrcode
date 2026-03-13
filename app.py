import io
import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps

import qrcode
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret-key')
app.config['ADMIN_USERNAME'] = os.getenv('ADMIN_USERNAME', 'admin')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin123')

FIELD_LABELS = {
    'production_date': '生产日期',
    'factory_date': '出厂日期',
    'team_name': '生成班组',
    'warehouse': '出厂仓库',
    'batch_code': '批次编码',
    'name': '酒类名称',
    'spec': '酒类规格',
    'abv': '酒精度数',
    'dealer': '经销商',
    'inspection_count': '鉴定次数',
}

CHECK_FIELDS = [
    ('check_production_date', '生产日期'),
    ('check_factory_date', '出厂日期'),
    ('check_team_name', '生成班组'),
    ('check_warehouse', '出厂仓库'),
    ('check_batch_code', '批次编码'),
    ('check_name', '酒类名称'),
    ('check_spec', '酒类规格'),
    ('check_abv', '酒精度数'),
    ('check_dealer', '经销商'),
    ('check_inspection_count', '鉴定次数'),
    ('check_chip', '加密芯片识别'),
    ('check_channel', '销售渠道对比'),
]


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS liquor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            spec TEXT,
            abv TEXT,
            production_date TEXT,
            factory_date TEXT,
            team_name TEXT,
            warehouse TEXT,
            batch_code TEXT,
            dealer TEXT,
            sales_company TEXT,
            sales_channel TEXT,
            inspection_time TEXT,
            inspection_result TEXT DEFAULT '已通过研判',
            inspection_count INTEGER DEFAULT 0,
            scan_count INTEGER DEFAULT 0,
            last_scan_at TEXT,
            status TEXT DEFAULT '正常',
            check_production_date INTEGER DEFAULT 1,
            check_factory_date INTEGER DEFAULT 1,
            check_team_name INTEGER DEFAULT 1,
            check_warehouse INTEGER DEFAULT 1,
            check_batch_code INTEGER DEFAULT 1,
            check_name INTEGER DEFAULT 1,
            check_spec INTEGER DEFAULT 1,
            check_abv INTEGER DEFAULT 1,
            check_dealer INTEGER DEFAULT 1,
            check_inspection_count INTEGER DEFAULT 1,
            check_chip INTEGER DEFAULT 1,
            check_channel INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )
    db.commit()
    db.close()


init_db()


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def parse_checkbox(name: str) -> int:
    return 1 if request.form.get(name) == 'on' else 0


def now_str() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_trace_code() -> str:
    db = get_db()
    while True:
        code = secrets.token_hex(8).upper()
        exists = db.execute('SELECT 1 FROM liquor WHERE trace_code = ?', (code,)).fetchone()
        if not exists:
            return code


@app.context_processor
def inject_globals():
    return {
        'check_fields': CHECK_FIELDS,
    }


@app.route('/')
def index():
    return redirect(url_for('admin_list')) if session.get('admin_logged_in') else redirect(url_for('admin_login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            flash('登录成功。', 'success')
            next_url = request.args.get('next') or url_for('admin_list')
            return redirect(next_url)
        flash('用户名或密码错误。', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    session.clear()
    flash('已退出登录。', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/liquors')
@admin_required
def admin_list():
    q = request.args.get('q', '').strip()
    db = get_db()
    if q:
        pattern = f'%{q}%'
        liquors = db.execute(
            '''
            SELECT * FROM liquor
            WHERE trace_code LIKE ?
               OR name LIKE ?
               OR batch_code LIKE ?
               OR dealer LIKE ?
            ORDER BY id DESC
            ''',
            (pattern, pattern, pattern, pattern),
        ).fetchall()
    else:
        liquors = db.execute('SELECT * FROM liquor ORDER BY id DESC').fetchall()
    return render_template('admin_list.html', liquors=liquors, q=q)


@app.route('/admin/liquors/new', methods=['GET', 'POST'])
@admin_required
def admin_new():
    if request.method == 'POST':
        db = get_db()
        trace_code = generate_trace_code()
        current_time = now_str()
        data = collect_form_data(trace_code=trace_code, created_at=current_time, updated_at=current_time)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        db.execute(f'INSERT INTO liquor ({columns}) VALUES ({placeholders})', tuple(data.values()))
        db.commit()
        flash('酒品已新增，二维码已可访问。', 'success')
        return redirect(url_for('admin_list'))
    return render_template('admin_form.html', liquor=None, action='new')


@app.route('/admin/liquors/<int:liquor_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit(liquor_id: int):
    db = get_db()
    liquor = db.execute('SELECT * FROM liquor WHERE id = ?', (liquor_id,)).fetchone()
    if not liquor:
        abort(404)

    if request.method == 'POST':
        data = collect_form_data(trace_code=liquor['trace_code'], created_at=liquor['created_at'], updated_at=now_str())
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        values = list(data.values()) + [liquor_id]
        db.execute(f'UPDATE liquor SET {set_clause} WHERE id = ?', values)
        db.commit()
        flash('酒品信息已更新。', 'success')
        return redirect(url_for('admin_list'))

    return render_template('admin_form.html', liquor=liquor, action='edit')


@app.route('/admin/liquors/<int:liquor_id>/delete', methods=['POST'])
@admin_required
def admin_delete(liquor_id: int):
    db = get_db()
    db.execute('DELETE FROM liquor WHERE id = ?', (liquor_id,))
    db.commit()
    flash('酒品记录已删除。', 'success')
    return redirect(url_for('admin_list'))


@app.route('/trace/<trace_code>')
def trace_page(trace_code: str):
    db = get_db()
    liquor = db.execute('SELECT * FROM liquor WHERE trace_code = ?', (trace_code,)).fetchone()
    if not liquor:
        abort(404)
    current_time = now_str()
    db.execute(
        'UPDATE liquor SET scan_count = COALESCE(scan_count, 0) + 1, last_scan_at = ?, updated_at = ? WHERE id = ?',
        (current_time, current_time, liquor['id']),
    )
    db.commit()
    liquor = db.execute('SELECT * FROM liquor WHERE trace_code = ?', (trace_code,)).fetchone()
    return render_template('trace.html', liquor=liquor)


@app.route('/qrcode/<trace_code>.png')
def qrcode_image(trace_code: str):
    db = get_db()
    liquor = db.execute('SELECT trace_code FROM liquor WHERE trace_code = ?', (trace_code,)).fetchone()
    if not liquor:
        abort(404)
    target_url = url_for('trace_page', trace_code=trace_code, _external=True)
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/seed-demo')
def seed_demo():
    db = get_db()
    existing = db.execute('SELECT COUNT(*) AS cnt FROM liquor').fetchone()['cnt']
    if existing > 0:
        return '已有数据，未重复插入。'

    current_time = now_str()
    trace_code = generate_trace_code()
    db.execute(
        '''
        INSERT INTO liquor (
            trace_code, name, spec, abv, production_date, factory_date,
            team_name, warehouse, batch_code, dealer, sales_company,
            sales_channel, inspection_time, inspection_result,
            inspection_count, scan_count, last_scan_at, status,
            check_production_date, check_factory_date, check_team_name,
            check_warehouse, check_batch_code, check_name, check_spec,
            check_abv, check_dealer, check_inspection_count,
            check_chip, check_channel, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            trace_code, '新飞天53%vol 500ml贵州茅台酒（1×6）RFID', '500ml', '53',
            '2020-06-09', '2020-06-18 20:48:54', '包装车间二班组', '贵阳三库',
            '2019-148', '廊坊中糖华洋实业有限公司', '贵阳三库（京东）', '京东',
            '2022-06-09 16:34:38', '已通过研判', 5, 0, '', '正常',
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, current_time, current_time
        ),
    )
    db.commit()
    return f'演示数据已插入，追溯码：{trace_code}'


def collect_form_data(trace_code: str, created_at: str, updated_at: str):
    return {
        'trace_code': trace_code,
        'name': request.form.get('name', '').strip(),
        'spec': request.form.get('spec', '').strip(),
        'abv': request.form.get('abv', '').strip(),
        'production_date': request.form.get('production_date', '').strip(),
        'factory_date': request.form.get('factory_date', '').strip(),
        'team_name': request.form.get('team_name', '').strip(),
        'warehouse': request.form.get('warehouse', '').strip(),
        'batch_code': request.form.get('batch_code', '').strip(),
        'dealer': request.form.get('dealer', '').strip(),
        'sales_company': request.form.get('sales_company', '').strip(),
        'sales_channel': request.form.get('sales_channel', '').strip(),
        'inspection_time': request.form.get('inspection_time', '').strip() or now_str(),
        'inspection_result': request.form.get('inspection_result', '已通过研判').strip() or '已通过研判',
        'inspection_count': int(request.form.get('inspection_count', '0') or 0),
        'scan_count': int(request.form.get('scan_count', '0') or 0),
        'last_scan_at': request.form.get('last_scan_at', '').strip(),
        'status': request.form.get('status', '正常').strip() or '正常',
        'check_production_date': parse_checkbox('check_production_date'),
        'check_factory_date': parse_checkbox('check_factory_date'),
        'check_team_name': parse_checkbox('check_team_name'),
        'check_warehouse': parse_checkbox('check_warehouse'),
        'check_batch_code': parse_checkbox('check_batch_code'),
        'check_name': parse_checkbox('check_name'),
        'check_spec': parse_checkbox('check_spec'),
        'check_abv': parse_checkbox('check_abv'),
        'check_dealer': parse_checkbox('check_dealer'),
        'check_inspection_count': parse_checkbox('check_inspection_count'),
        'check_chip': parse_checkbox('check_chip'),
        'check_channel': parse_checkbox('check_channel'),
        'created_at': created_at,
        'updated_at': updated_at,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
