"""Future collector writes only; no historical repairs or model changes.

Event rules follow the reviewed v4 local preflight. Device codes are self-declared,
not browser fingerprints or proof of physical hardware.
"""
import math
import re
import hashlib
import json

DEVICE_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,39}\Z')
REQUEST_RE = re.compile(r'[0-9a-f]{32}\Z')
EXPECTED = list('.tie5Roanl') + ['Enter']
MODIFIERS = {'shift', 'control', 'alt', 'meta', 'capslock', 'altgraph'}
TYPES = {'down': 'down', 'keydown': 'down', 'up': 'up', 'keyup': 'up'}


def device_code(value):
    if not isinstance(value, str) or not DEVICE_RE.fullmatch(value):
        raise ValueError('device_id_invalid')
    return value


def request_code(value):
    if not isinstance(value, str) or not REQUEST_RE.fullmatch(value):
        raise ValueError('request_id_invalid')
    return value


def sample_digest(session, device, events):
    payload = {'session': session, 'device_id': device, 'events': events}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def find_replay(records, request_id, digest):
    matches = [r for r in records if isinstance(r, dict) and r.get('request_id') == request_id]
    if len(matches) > 1:
        raise ValueError('request_history_ambiguous')
    if not matches:
        return None
    row = matches[0]
    try:
        stored = sample_digest(row['session'], row['device_id'], row['events'])
    except (KeyError, ValueError, TypeError):
        raise ValueError('request_history_ambiguous') from None
    if stored != row.get('request_payload_sha256'):
        raise ValueError('request_history_ambiguous')
    if digest != stored:
        raise ValueError('request_id_payload_conflict')
    return row


def event_issues(events):
    if not isinstance(events, list) or not events:
        return ['events_missing_or_invalid']
    if len(events) > 200:
        return ['events_too_many']
    issues, active, typed = set(), {}, []
    previous = -float('inf')
    for event in events:
        if not isinstance(event, dict):
            issues.add('event_not_object'); continue
        key, kind, t = event.get('key'), event.get('type'), event.get('t')
        if not isinstance(key, str) or not key or not isinstance(kind, str) or kind not in TYPES:
            issues.add('event_key_or_type_invalid'); continue
        try:
            finite = type(t) in (int, float) and math.isfinite(t) and t >= 0
        except OverflowError:
            finite = False
        if not finite:
            issues.add('event_time_invalid'); continue
        if t < previous: issues.add('event_order_not_monotonic')
        previous = t
        norm = 'enter' if key.lower() in ('enter', 'return') else key.lower()
        code = event.get('code')
        if code is not None and (not isinstance(code, str) or not code.strip() or len(code) > 40):
            issues.add('event_code_invalid'); continue
        identity = ('code', code) if code is not None else ('key', norm)
        if TYPES[kind] == 'down':
            if identity in active:
                issues.add('repeated_down_without_up'); continue
            active[identity] = (t, norm)
            if norm not in MODIFIERS:
                typed.append('Enter' if norm == 'enter' else key)
        else:
            start = active.pop(identity, None)
            if start is None:
                issues.add('up_without_down')
            else:
                if t < start[0]: issues.add('negative_hold')
                if norm != start[1]: issues.add('key_changed_on_same_code')
    if active: issues.add('down_without_up')
    if typed != EXPECTED: issues.add('phrase_or_case_mismatch')
    return sorted(issues)


def next_rep(records, participant, session):
    """Keep gaps, reject ambiguous histories; call under the existing write lock."""
    seen = set()
    for row in records:
        if not isinstance(row, dict): raise ValueError('collection_history_invalid')
        if row.get('session') != session: continue
        rep = row.get('rep')
        if row.get('participant_id') != participant or type(row.get('session')) is not int or type(rep) is not int or rep < 1:
            raise ValueError('collection_history_invalid')
        if rep in seen: raise ValueError('collection_history_duplicate_key')
        seen.add(rep)
    return max(seen, default=0) + 1, len(seen)
