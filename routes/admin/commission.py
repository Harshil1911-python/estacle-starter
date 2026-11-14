"""Admin commission routes."""

from flask import render_template

from core.db import get_db
from core.helpers import (
    login_required, role_required, get_setting, format_money
)
from routes.admin import admin


@admin.route('/admin/commission')
@login_required
@role_required('admin')
def admin_commission():
    db = get_db()
    deals = db.execute(
        """SELECT d.*, p.title as property_title, u.full_name as agent_name
           FROM deals d LEFT JOIN properties p ON d.property_id = p.id
           LEFT JOIN users u ON d.agent_id = u.id
           WHERE d.stage = 'closed'
           ORDER BY d.updated_at DESC"""
    ).fetchall()
    total_value = sum((d['value'] or 0) for d in deals)
    total_comm = sum(((d['value'] or 0) * (d['commission_rate'] or 0) / 100) for d in deals)
    currency = get_setting('currency', 'INR')
    return render_template(
        'admin_commission.html', deals=deals, total_value=total_value, total_comm=total_comm,
        currency=currency, format_money=format_money
    )
