"""A JSON backed database.

It should never be used in production because it is not thread safe.
"""

import json

import click
from flask import current_app
from flask import g
import flaskr


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        with open(current_app.config["DATABASE"], 'r', encoding='utf-8') as f:
            g.db = json.load(f)

    return g.db

def commit(db=None):
    if db is None:
        db = g.db
    with open(current_app.config["DATABASE"], 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, separators=(',', ': '), sort_keys=True)

def get_new_id(table):
    """Return a new integer ID that is not used in table."""
    i = 1
    for entry in table:
        i = max(entry['id'], i)
    return (i + 1)

def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        commit(db)


def init_db():
    """Clear existing data and create new tables."""
    commit({
        'users': [],
        'posts': []
    })


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    # Patch Working outside of application context RuntimeError
    app = flaskr.create_app()
    with app.app_context():
        init_db()
        click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
