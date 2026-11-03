"""Admin -> Phrases: the whole phrase library as one CSV file (download), and Spanish / Italian phrases from a CSV
file (upload). Admins only.

The file has one row per phrase per language: Lang (fr, en, es, it), LineID, CategoryID, Availability, then one column
per mood (tones.KEYS: Basic ... Stupid). The download holds French and English (and any Spanish and Italian so far),
so a translator can add "es" / "it" rows, or the same file can be sent back with translations added. The upload only
writes Spanish and Italian rows: a row with the same LineID is updated (empty cells leave the old text), a new LineID
is added. French and English rows in the file are skipped, so the live French library can't be changed by accident.
"""
import csv
import io

import anvil
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Phrases, langs, tones

HEAD = ["Lang", "LineID", "CategoryID", "Availability"] + tones.KEYS
UPLOAD = ("es", "it")
MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000


def _num(v):
    try:
        return int(float(str(v).strip()))
    except Exception:
        return None


@anvil.server.callable(require_user=True)
def admin_phrases_csv():
    """Every phrase in every language as a CSV file (UTF-8, opens in Excel and Google Sheets)."""
    C.require_admin()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(HEAD)
    sources = [("fr", Phrases.rows("fr")), ("en", list(app_tables.frenchsentences_translation.search()))]
    sources += [(c, Phrases.rows(c)) for c in langs.CODES if c != "fr"]
    for code, found in sources:
        for r in sorted([r for r in found if r["LineID"] is not None], key=lambda r: int(r["LineID"])):
            w.writerow([code, int(r["LineID"]), "" if r["CategoryID"] is None else int(r["CategoryID"]),
                        r["Availability"] or ""] + [(r[k] or "").strip() for k in tones.KEYS])
    data = ("﻿" + out.getvalue()).encode("utf-8")  # the BOM tells Excel it's UTF-8 (accents)
    return anvil.BlobMedia("text/csv", data, name="parapeet-phrases-%s.csv" % C.now().date().isoformat())


def _read(media):
    raw = media.get_bytes() if hasattr(media, "get_bytes") else media
    if not raw:
        raise ValueError("The file is empty.")
    if len(raw) > MAX_BYTES:
        raise ValueError("The file is too big (5 MB at most).")
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Save the file as CSV UTF-8 and try again.")
    sample = text[:4000]
    delim = ";" if sample.count(";") > sample.count(",") else ","  # Excel in some countries saves with ;
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


@anvil.server.callable(require_user=True)
def admin_upload_phrases(media):
    """Spanish and Italian rows of a CSV file -> SpanishSentences / ItalianSentences.
    Returns {ok, added, updated, skipped, problems: [first 20 problems], by_lang: {es: n, it: n}}."""
    C.require_admin()
    try:
        rows = _read(media)
    except ValueError as e:
        return C.fail(str(e))
    except Exception:
        return C.fail("That doesn't look like a CSV file. Save it as CSV UTF-8 and try again.")
    if not rows:
        return C.fail("The file has no rows.")
    cols = set(k.strip() for k in rows[0].keys() if k)
    if not {"Lang", "LineID", "Basic"} <= cols:
        return C.fail("The first line must name the columns: Lang, LineID, Basic ... (download the phrases to see the layout).")
    if len(rows) > MAX_ROWS:
        return C.fail("Too many rows (%d at most per file)." % MAX_ROWS)
    tables = {}
    for code in UPLOAD:
        t = Phrases.table(code)
        if t is not None:
            tables[code] = t
    added = updated = skipped = 0
    by_lang: dict = {}
    problems = []
    for n, raw in enumerate(rows, start=2):
        row = dict(((k or "").strip(), (v or "").strip() if isinstance(v, str) else "") for k, v in raw.items())
        code = row.get("Lang", "").lower()
        if code not in UPLOAD:
            skipped += 1
            continue
        if code not in tables:
            problems.append("Line %d: the %s table doesn't exist yet (accept the Schema Mismatch in the Anvil editor)." % (n, langs.name(code)))
            continue
        line_id = _num(row.get("LineID"))
        if line_id is None:
            problems.append("Line %d: LineID must be a number." % n)
            continue
        texts = dict((k, C.text(row.get(k), 600)) for k in tones.KEYS if row.get(k))
        cat = _num(row.get("CategoryID"))
        avail = row.get("Availability", "").lower()
        if avail and avail not in ("basic", "free", "premium"):
            problems.append("Line %d: Availability must be basic, free or premium (or empty)." % n)
            continue
        extra = {}
        if cat is not None:
            extra["CategoryID"] = cat
        if avail:
            extra["Availability"] = avail
        t = tables[code]
        existing = None
        for r in t.search(LineID=line_id):
            existing = r
            break
        if existing is None:
            if not texts.get("Basic"):
                problems.append("Line %d: a new phrase needs its Basic (neutral) text." % n)
                continue
            t.add_row(LineID=line_id, **dict(texts, **extra))
            added += 1
        else:
            existing.update(**dict(texts, **extra))
            updated += 1
        by_lang[code] = by_lang.get(code, 0) + 1
    if not (added or updated) and problems:
        return {"ok": False, "error": problems[0], "problems": problems[:20]}
    return C.ok(added=added, updated=updated, skipped=skipped, problems=problems[:20], by_lang=by_lang)
