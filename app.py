"""
CWSRBS - Co-Working Space Resource Booking System
Backend: Python Flask + SQLite
"""
import sqlite3, os, datetime
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
import bcrypt

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['JWT_SECRET_KEY'] = 'cwsrbs-demo-secret-2026'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=8)

CORS(app)
jwt = JWTManager(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'cwsrbs.db')

# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name  TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role       TEXT NOT NULL DEFAULT 'member',
        membership TEXT NOT NULL DEFAULT 'standard',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS resource_types (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT NOT NULL DEFAULT '🏢'
    );

    CREATE TABLE IF NOT EXISTS resources (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        type_id     INTEGER NOT NULL REFERENCES resource_types(id),
        name        TEXT NOT NULL,
        capacity    INTEGER NOT NULL DEFAULT 1,
        hourly_rate REAL NOT NULL,
        location    TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'available',
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        resource_id INTEGER NOT NULL REFERENCES resources(id),
        start_dt    TEXT NOT NULL,
        end_dt      TEXT NOT NULL,
        total_cost  REAL NOT NULL,
        status      TEXT NOT NULL DEFAULT 'confirmed',
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS payments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id  INTEGER NOT NULL UNIQUE REFERENCES bookings(id),
        amount      REAL NOT NULL,
        method      TEXT NOT NULL DEFAULT 'card',
        tx_ref      TEXT,
        status      TEXT NOT NULL DEFAULT 'paid',
        paid_at     TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # Seed resource types
    db.execute("INSERT OR IGNORE INTO resource_types(id,name,icon) VALUES(1,'Hot Desk','🪑')")
    db.execute("INSERT OR IGNORE INTO resource_types(id,name,icon) VALUES(2,'Private Office','🏢')")
    db.execute("INSERT OR IGNORE INTO resource_types(id,name,icon) VALUES(3,'Meeting Room','📋')")
    db.execute("INSERT OR IGNORE INTO resource_types(id,name,icon) VALUES(4,'Event Space','🎤')")

    # Seed resources
    seed_resources = [
        (1,'Hot Desk A1',1,8.50,'Floor 1','Perfect for solo focused work'),
        (1,'Hot Desk A2',1,8.50,'Floor 1','Quiet corner near window'),
        (1,'Hot Desk B1',1,8.50,'Floor 2','Collaborative zone with standing option'),
        (2,'The Studio',4,35.00,'Floor 2','Private 4-person office with whiteboards'),
        (2,'The Loft',6,55.00,'Floor 3','Panoramic views, ideal for small teams'),
        (3,'Boardroom Alpha',12,75.00,'Floor 1','Full AV, video conferencing suite'),
        (3,'Meeting Pod Zeta',4,30.00,'Floor 2','Soundproofed, TV screen included'),
        (3,'Huddle Room',2,20.00,'Ground','Quick catch-up space, no booking fee'),
        (4,'Main Hall',80,200.00,'Ground','For workshops, pitch events, launches'),
    ]
    for r in seed_resources:
        db.execute("""INSERT OR IGNORE INTO resources(type_id,name,capacity,hourly_rate,location,description)
                      VALUES(?,?,?,?,?,?)""", r)

    # Seed admin user  (password: admin123)
    pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
    db.execute("""INSERT OR IGNORE INTO users(id,first_name,last_name,email,password_hash,role,membership)
                  VALUES(1,'Admin','User','admin@cwsrbs.com',?,'admin','premium')""", (pw,))

    # Seed demo member  (password: member123)
    pw2 = bcrypt.hashpw(b'member123', bcrypt.gensalt()).decode()
    db.execute("""INSERT OR IGNORE INTO users(id,first_name,last_name,email,password_hash,role,membership)
                  VALUES(2,'Jane','Smith','jane@demo.com',?,'member','standard')""", (pw2,))

    db.commit()
    db.close()
    print("✅ Database initialised at", DB_PATH)

# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    d = request.json or {}
    required = ['first_name','last_name','email','password']
    if not all(d.get(k) for k in required):
        return jsonify(error='All fields required'), 400
    db = get_db()
    if db.execute('SELECT id FROM users WHERE email=?', (d['email'],)).fetchone():
        return jsonify(error='Email already registered'), 409
    pw_hash = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        'INSERT INTO users(first_name,last_name,email,password_hash) VALUES(?,?,?,?)',
        (d['first_name'], d['last_name'], d['email'], pw_hash)
    )
    db.commit()
    token = create_access_token(identity=str(cur.lastrowid))
    user = db.execute('SELECT * FROM users WHERE id=?', (cur.lastrowid,)).fetchone()
    return jsonify(token=token, user=_user_dict(user)), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    d = request.json or {}
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=?', (d.get('email',''),)).fetchone()
    if not user or not bcrypt.checkpw(d.get('password','').encode(), user['password_hash'].encode()):
        return jsonify(error='Invalid email or password'), 401
    token = create_access_token(identity=str(user['id']))
    return jsonify(token=token, user=_user_dict(user))

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (get_jwt_identity(),)).fetchone()
    return jsonify(_user_dict(user))

def _user_dict(u):
    return dict(id=u['id'], first_name=u['first_name'], last_name=u['last_name'],
                email=u['email'], role=u['role'], membership=u['membership'],
                created_at=u['created_at'])

# ─── Resources ───────────────────────────────────────────────────────────────

@app.route('/api/resources', methods=['GET'])
def get_resources():
    db = get_db()
    rows = db.execute("""
        SELECT r.*, t.name as type_name, t.icon
        FROM resources r JOIN resource_types t ON r.type_id=t.id
        WHERE r.status='available'
        ORDER BY r.type_id, r.name
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/resources/availability', methods=['GET'])
def check_availability():
    rid   = request.args.get('resource_id')
    start = request.args.get('start')
    end   = request.args.get('end')
    if not all([rid, start, end]):
        return jsonify(error='resource_id, start, end required'), 400
    db = get_db()
    clash = db.execute("""
        SELECT id FROM bookings
        WHERE resource_id=? AND status='confirmed'
          AND NOT (end_dt <= ? OR start_dt >= ?)
    """, (rid, start, end)).fetchone()
    return jsonify(available=clash is None)

@app.route('/api/resource-types', methods=['GET'])
def get_types():
    db = get_db()
    rows = db.execute('SELECT * FROM resource_types').fetchall()
    return jsonify([dict(r) for r in rows])

# ─── Bookings ────────────────────────────────────────────────────────────────

@app.route('/api/bookings', methods=['GET'])
@jwt_required()
def get_bookings():
    uid = get_jwt_identity()
    db  = get_db()
    rows = db.execute("""
        SELECT b.*, r.name as resource_name, r.location,
               t.icon, t.name as type_name,
               u.first_name, u.last_name, u.email
        FROM bookings b
        JOIN resources r ON b.resource_id=r.id
        JOIN resource_types t ON r.type_id=t.id
        JOIN users u ON b.user_id=u.id
        WHERE b.user_id=?
        ORDER BY b.start_dt DESC
    """, (uid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    uid = get_jwt_identity()
    d   = request.json or {}
    required = ['resource_id','start_dt','end_dt']
    if not all(d.get(k) for k in required):
        return jsonify(error='resource_id, start_dt, end_dt required'), 400

    db  = get_db()
    res = db.execute('SELECT * FROM resources WHERE id=? AND status="available"',
                     (d['resource_id'],)).fetchone()
    if not res:
        return jsonify(error='Resource not found or unavailable'), 404

    # Check clash
    clash = db.execute("""
        SELECT id FROM bookings WHERE resource_id=? AND status='confirmed'
          AND NOT (end_dt<=? OR start_dt>=?)
    """, (d['resource_id'], d['start_dt'], d['end_dt'])).fetchone()
    if clash:
        return jsonify(error='Resource already booked for this time'), 409

    # Calculate cost
    fmt = '%Y-%m-%dT%H:%M'
    try:
        s = datetime.datetime.strptime(d['start_dt'], fmt)
        e = datetime.datetime.strptime(d['end_dt'],   fmt)
    except ValueError:
        return jsonify(error='Invalid datetime format. Use YYYY-MM-DDTHH:MM'), 400
    if e <= s:
        return jsonify(error='End time must be after start time'), 400
    hours = (e - s).total_seconds() / 3600
    cost  = round(res['hourly_rate'] * hours, 2)

    cur = db.execute("""
        INSERT INTO bookings(user_id,resource_id,start_dt,end_dt,total_cost)
        VALUES(?,?,?,?,?)
    """, (uid, d['resource_id'], d['start_dt'], d['end_dt'], cost))
    bid = cur.lastrowid

    # Simulate payment record
    import random, string
    tx = 'TXN-' + ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))
    db.execute("INSERT INTO payments(booking_id,amount,tx_ref) VALUES(?,?,?)", (bid, cost, tx))
    db.commit()

    booking = db.execute("""
        SELECT b.*, r.name as resource_name, r.location, t.icon, t.name as type_name
        FROM bookings b JOIN resources r ON b.resource_id=r.id
        JOIN resource_types t ON r.type_id=t.id WHERE b.id=?
    """, (bid,)).fetchone()
    return jsonify(dict(booking)), 201

@app.route('/api/bookings/<int:bid>', methods=['DELETE'])
@jwt_required()
def cancel_booking(bid):
    uid = get_jwt_identity()
    db  = get_db()
    b   = db.execute('SELECT * FROM bookings WHERE id=? AND user_id=?', (bid, uid)).fetchone()
    if not b:
        return jsonify(error='Booking not found'), 404
    if b['status'] == 'cancelled':
        return jsonify(error='Already cancelled'), 400
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    db.execute("UPDATE payments SET status='refunded' WHERE booking_id=?", (bid,))
    db.commit()
    return jsonify(message='Booking cancelled successfully')

# ─── Admin Routes ─────────────────────────────────────────────────────────────

def require_admin():
    db   = get_db()
    user = db.execute('SELECT role FROM users WHERE id=?', (get_jwt_identity(),)).fetchone()
    return user and user['role'] == 'admin'

@app.route('/api/admin/resources', methods=['POST'])
@jwt_required()
def admin_add_resource():
    if not require_admin(): return jsonify(error='Admin only'), 403
    d  = request.json or {}
    db = get_db()
    cur = db.execute("""
        INSERT INTO resources(type_id,name,capacity,hourly_rate,location,description)
        VALUES(?,?,?,?,?,?)
    """, (d['type_id'],d['name'],d['capacity'],d['hourly_rate'],d['location'],d.get('description','')))
    db.commit()
    return jsonify(id=cur.lastrowid, message='Resource added'), 201

@app.route('/api/admin/resources/<int:rid>', methods=['PUT'])
@jwt_required()
def admin_update_resource(rid):
    if not require_admin(): return jsonify(error='Admin only'), 403
    d  = request.json or {}
    db = get_db()
    db.execute("""UPDATE resources SET name=?,hourly_rate=?,status=?,capacity=?,location=?
                  WHERE id=?""",
               (d['name'],d['hourly_rate'],d['status'],d['capacity'],d['location'],rid))
    db.commit()
    return jsonify(message='Updated')

@app.route('/api/admin/resources/<int:rid>', methods=['DELETE'])
@jwt_required()
def admin_delete_resource(rid):
    if not require_admin(): return jsonify(error='Admin only'), 403
    db = get_db()
    db.execute("UPDATE resources SET status='deactivated' WHERE id=?", (rid,))
    db.commit()
    return jsonify(message='Resource deactivated')

@app.route('/api/admin/all-bookings', methods=['GET'])
@jwt_required()
def admin_all_bookings():
    if not require_admin(): return jsonify(error='Admin only'), 403
    db = get_db()
    rows = db.execute("""
        SELECT b.*, r.name as resource_name, t.icon,
               u.first_name, u.last_name, u.email
        FROM bookings b
        JOIN resources r ON b.resource_id=r.id
        JOIN resource_types t ON r.type_id=t.id
        JOIN users u ON b.user_id=u.id
        ORDER BY b.created_at DESC LIMIT 100
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/reports', methods=['GET'])
@jwt_required()
def admin_reports():
    if not require_admin(): return jsonify(error='Admin only'), 403
    db = get_db()
    total_bookings    = db.execute("SELECT COUNT(*) c FROM bookings WHERE status='confirmed'").fetchone()['c']
    total_revenue     = db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='paid'").fetchone()['s']
    total_members     = db.execute("SELECT COUNT(*) c FROM users WHERE role='member'").fetchone()['c']
    top_resources     = db.execute("""
        SELECT r.name, COUNT(b.id) bookings, SUM(b.total_cost) revenue
        FROM bookings b JOIN resources r ON b.resource_id=r.id
        WHERE b.status='confirmed'
        GROUP BY r.id ORDER BY bookings DESC LIMIT 5
    """).fetchall()
    monthly           = db.execute("""
        SELECT strftime('%Y-%m', start_dt) month, COUNT(*) bookings, SUM(total_cost) revenue
        FROM bookings WHERE status='confirmed'
        GROUP BY month ORDER BY month DESC LIMIT 6
    """).fetchall()
    return jsonify(
        total_bookings=total_bookings,
        total_revenue=round(float(total_revenue),2),
        total_members=total_members,
        top_resources=[dict(r) for r in top_resources],
        monthly=[dict(r) for r in monthly]
    )

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    if not require_admin(): return jsonify(error='Admin only'), 403
    db = get_db()
    rows = db.execute("""
        SELECT u.*, COUNT(b.id) total_bookings
        FROM users u LEFT JOIN bookings b ON u.id=b.user_id AND b.status='confirmed'
        GROUP BY u.id ORDER BY u.created_at DESC
    """).fetchall()
    return jsonify([_user_dict(r) | {'total_bookings': r['total_bookings']} for r in rows])

# ─── Serve Frontend ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 CWSRBS running at http://localhost:{port}")
    print("   Admin login:  admin@cwsrbs.com / admin123")
    print("   Demo member:  jane@demo.com / member123\n")
    app.run(debug=True, host='0.0.0.0', port=port)

# ─── Render/Gunicorn compatibility ──────────────────────────────────────────
# When deployed on Render, gunicorn calls `app` directly (not __main__)
# So we must initialise the DB here too.
import os as _os
if _os.environ.get('RENDER'):
    init_db()
