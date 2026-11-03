import sqlite3

from fastapi import Request


def get_connection(request: Request) -> sqlite3.Connection:
    return request.app.state.connection


def get_upload_dir(request: Request) -> str:
    return request.app.state.upload_dir