import uuid
from datetime import datetime, timedelta

from flask import session

active_sessions = {}


def set_session(key: str, value, seconds: int = 0):
    session[key] = {
        "value": value,
        "expires_at": seconds
        if seconds == 0
        else (datetime.now() + timedelta(seconds=seconds)).isoformat(),
    }
    print(session[key])


def get_session(key: str):
    if not key or not isinstance(key, str):
        return None
    value = session.get(key, None)
    if session:
        if isinstance(value, dict):
            expires_at = value.get("expires_at", 0)
            value = value.get("value")
            if expires_at != 0 and datetime.now() > datetime.fromisoformat(expires_at):
                value = None
    return value


def login(userid: str, user, timeout: int = 0):
    userid = uuid.uuid4()
    if userid in active_sessions:
        session.clear()
    session_id = str(uuid.uuid4())
    active_sessions[userid] = session_id
    set_session("login_userid", userid)
    set_session("login_session_id", session_id)
    set_session("userinfo", user, timeout)


def login_out():
    # if userid :
    #     session.pop(userid, None)
    session.clear()


def userinfo():

    return get_session("userinfo")
