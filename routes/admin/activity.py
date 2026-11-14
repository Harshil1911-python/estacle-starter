"""Admin activity log routes."""

from flask import render_template

from core.db import get_db, migrate_db
from core.helpers import login_required, role_required
from routes.admin import admin


@admin.route('/admin/activity')
@login_required
@role_required('admin')
def admin_activity():
    db = get_db()
    logs = db.execute(
        "SELECT a.*, u.full_name as user_name FROM activity_log a "
        "LEFT JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT 100"
    ).fetchall()
    return render_template('admin_activity.html', logs=logs)


@admin.route('/admin/api/notifications/today')
@login_required
@role_required('admin')
def admin_notifications_today():
    """Items created today: properties, clients, deals, users, leads, appointments, tasks."""
    from flask import jsonify
    from datetime import datetime
    db = get_db()
    migrate_db()
    today = datetime.now().strftime('%Y-%m-%d')
    items = []

    def add_rows(sql, kind, label_key='title'):
        try:
            rows = db.execute(sql, (today,)).fetchall()
        except Exception:
            return
        for r in rows:
            d = dict(r)
            title = d.get(label_key) or d.get('full_name') or d.get('title') or ('#%s' % d.get('id'))
            items.append({
                'kind': kind,
                'id': d.get('id'),
                'title': title,
                'created_at': d.get('created_at'),
                'meta': d.get('meta') or d.get('stage') or d.get('status') or '',
            })

    add_rows(
        "SELECT id, title, status as meta, created_at FROM properties WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 30",
        'property', 'title')
    add_rows(
        "SELECT id, full_name, status as meta, created_at FROM clients WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 30",
        'client', 'full_name')
    add_rows(
        "SELECT id, title, stage as meta, created_at FROM deals WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 30",
        'deal', 'title')
    add_rows(
        "SELECT id, full_name, role as meta, created_at FROM users WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 20",
        'user', 'full_name')
    add_rows(
        "SELECT id, title, status as meta, created_at FROM tasks WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 20",
        'task', 'title')
    try:
        rows = db.execute(
            "SELECT id, appointment_date as created_at, status as meta, notes as title FROM appointments WHERE date(created_at)=date(?) ORDER BY created_at DESC LIMIT 20",
            (today,),
        ).fetchall()
        for r in rows:
            d = dict(r)
            items.append({
                'kind': 'appointment',
                'id': d.get('id'),
                'title': d.get('title') or ('Appointment #%s' % d.get('id')),
                'created_at': d.get('created_at'),
                'meta': d.get('meta') or '',
            })
    except Exception:
        pass

    # sort by created_at desc
    def key(it):
        return str(it.get('created_at') or '')
    items.sort(key=key, reverse=True)
    return jsonify({'ok': True, 'date': today, 'count': len(items), 'items': items[:50]})
