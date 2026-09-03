"""
Admin module for the AI Registration Assistant.
Provides a protected admin dashboard to view, filter, delete,
and export registration records saved by the chatbot.

Note: This is a lightweight demo authentication (no hashed passwords,
no HTTPS enforcement) intended for internship demonstration purposes.
"""

import json
import os
from collections import Counter
from io import StringIO

import csv
from functools import wraps

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

# -------------------------------------------------------------------
# Admin configuration
# -------------------------------------------------------------------
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Path to the registration data file (same file the chatbot writes to).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRATIONS_FILE = os.path.join(BASE_DIR, 'registrations.json')


def load_registrations():
    """Load registration records from the JSON file."""
    try:
        with open(REGISTRATIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_registrations(records):
    """Persist registration records back to the JSON file."""
    with open(REGISTRATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)


def is_authenticated():
    """Check whether the current session is logged in as admin."""
    return session.get('is_admin') is True


def login_required(view):
    """Decorator: redirect unauthenticated visitors to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('admin.login'))
        return view(*args, **kwargs)
    return wrapped


# -------------------------------------------------------------------
# Flask blueprint
# -------------------------------------------------------------------
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Welcome back, admin!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin_login.html')


@admin_bp.route('/logout')
def logout():
    """Log the admin out."""
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    """Main admin dashboard: table of registrations + analytics."""
    records = load_registrations()

    # Search / filter
    query = request.args.get('q', '').strip().lower()
    if query:
        records = [
            r for r in records
            if query in str(r.get('name', '')).lower()
            or query in str(r.get('email', '')).lower()
            or query in str(r.get('field', '')).lower()
            or query in str(r.get('experience', '')).lower()
        ]

    # Analytics
    total = len(records)
    fields = Counter(r.get('field', 'Unknown') for r in records)
    experiences = Counter(r.get('experience', 'Unknown') for r in records)

    return render_template(
        'admin_dashboard.html',
        records=records,
        total=total,
        fields=fields.most_common(),
        experiences=experiences.most_common(),
        query=query,
    )


@admin_bp.route('/delete/<int:index>', methods=['POST'])
@login_required
def delete(index):
    """Delete a registration record by its index in the list."""
    records = load_registrations()
    if 0 <= index < len(records):
        removed = records.pop(index)
        save_registrations(records)
        flash(f"Deleted {removed.get('name', 'record')}.", 'info')
    else:
        flash('Record not found.', 'error')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/export')
@login_required
def export():
    """Export all registrations as a CSV download."""
    records = load_registrations()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['name', 'email', 'field', 'experience', 'registered_at'],
        extrasaction='ignore'
    )
    writer.writeheader()
    writer.writerows(records)

    return _csv_response(output.getvalue())


def _csv_response(csv_text, filename='registrations.csv'):
    from flask import Response
    return Response(
        csv_text,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )