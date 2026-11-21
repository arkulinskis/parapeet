"""Phrase finder: "What do you need to say, and to whom?" Plain Python (no Anvil imports), shared by the browser
(Pages/Find searches the phrases this person can open) and the server (Phrases.count_locked_matches counts the locked
ones that match, without sending their text). tools/testing/test_server.py copies it next to the server modules.

A phrase is the usual {"id", "fr": {mood: text}, "en": {mood: text}} ("fr" = the language being learned, see langs.py).
Scoring: every word of the search (plus a few English synonyms, worth half) is looked up in the English of every mood
(2 points in the neutral and the chosen mood, 1 in the others) and in the phrase's own language (2 points). Words of 3+
letters also match the start of longer words ("meet" finds "meeting"). Phrases that match more of the search's words
come first; the whole search found word for word in an English line adds a bonus.
Words that name the listener ("boss", "client", "wife") pick the mood instead of being searched (listener()).
"""
from . import tones

ACCENTS = [("à", "a"), ("â", "a"), ("ä", "a"), ("á", "a"), ("ã", "a"), ("ç", "c"),
           ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("î", "i"), ("ï", "i"),
           ("í", "i"), ("ì", "i"), ("ô", "o"), ("ö", "o"), ("ó", "o"), ("ò", "o"),
           ("õ", "o"), ("ù", "u"), ("û", "u"), ("ü", "u"), ("ú", "u"), ("ñ", "n"),
           ("œ", "oe"), ("æ", "ae"), ("ÿ", "y")]
PUNCT = ".,;:!?()[]{}\"'’‘«»“”…¿¡-–—/\\*&+=<>#@%^_~`$"

STOP = set("""a an the to of in on at for and or but is are am be been was were it this that these those i you he she we
they me my your our his her their its with as by from so if do does did not no can could would will shall should may
might must have has had just very really please some any all there here what how when where who why about up out into
than then too also let lets get got im ive ill id dont doesnt didnt cant wont youre were us them him one more much like
make say tell want something someone way thing things know go going s t m d ll re ve""".split())

# Words that say who you're talking to: they choose the mood (tones.KEYS) instead of being searched for.
LISTENERS = {
    "neutral": "Basic", "anyone": "Basic", "stranger": "Basic",
    "colleague": "Colleague", "colleagues": "Colleague", "coworker": "Colleague", "coworkers": "Colleague",
    "teammate": "Colleague", "team": "Colleague",
    "client": "Client", "clients": "Client", "customer": "Client", "customers": "Client",
    "boss": "Boss", "manager": "Boss", "supervisor": "Boss", "director": "Boss", "ceo": "Boss",
    "hothead": "Agressive", "angry": "Agressive", "furious": "Agressive", "mad": "Agressive",
    "frustrated": "Frustrated", "tense": "Frustrated", "stressed": "Frustrated",
    "sad": "Sad", "comfort": "Sad", "crying": "Sad", "grieving": "Sad",
    "partner": "Lover", "lover": "Lover", "wife": "Lover", "husband": "Lover", "girlfriend": "Lover",
    "boyfriend": "Lover", "darling": "Lover", "honey": "Lover", "sweetheart": "Lover",
    "admiring": "Impressed", "impressed": "Impressed", "admire": "Impressed", "compliment": "Impressed",
    "silly": "Stupid", "funny": "Stupid", "joke": "Stupid", "goofy": "Stupid",
}

SYNONYMS = [
    ["sorry", "apologize", "apologise", "apology", "apologies", "excuse", "forgive", "pardon"],
    ["thanks", "thank", "grateful", "appreciate", "thankful", "gratitude"],
    ["help", "assist", "assistance", "support"],
    ["meet", "meeting", "meetings"],
    ["late", "delay", "delayed", "behind"],
    ["problem", "issue", "trouble", "mistake", "error"],
    ["email", "mail", "message"],
    ["hello", "hi", "morning", "greet"],
    ["bye", "goodbye", "leave", "leaving"],
    ["lunch", "eat", "food", "hungry", "dinner"],
    ["coffee", "break", "tea"],
    ["deadline", "due", "finish"],
    ["money", "pay", "salary", "price", "cost", "budget"],
    ["idea", "suggest", "suggestion", "propose"],
    ["question", "ask"],
    ["agree", "agreed"],
    ["report", "document", "file"],
    ["tired", "exhausted", "sleep"],
    ["happy", "glad", "pleased", "delighted"],
    ["wait", "waiting", "moment"],
    ["calm", "relax", "breathe"],
]
GROUP: dict = {}
for _grp in SYNONYMS:
    for _w in _grp:
        GROUP[_w] = _grp

# Suggestion chips, in this order, kept only when they match something; "thank" reads better as "thank you".
CURATED = ["late", "help", "meeting", "thank", "sorry", "project", "coffee", "lunch", "pen", "report", "email",
           "deadline", "question", "idea", "weekend", "tired", "calm", "hello"]
CHIP_TEXT = {"thank": "thank you"}


def norm(text):
    """Lower case, accents off, punctuation turned into spaces ("|" is kept: index() uses it as a separator)."""
    s = (text or "").lower()
    for a, b in ACCENTS:
        if a in s:
            s = s.replace(a, b)
    for ch in PUNCT:
        if ch in s:
            s = s.replace(ch, " ")
    return s


def words(text):
    return [w for w in norm(text).split() if w]


def listener(query):
    """The mood a search names ("late boss" -> "Boss"), or None."""
    for w in words(query):
        if w in LISTENERS:
            return LISTENERS[w]
    return None


def terms(query):
    """The words of a search worth looking up (no small words, no listener words)."""
    ws = [w for w in words(query) if w not in LISTENERS]
    content = [w for w in ws if w not in STOP and len(w) > 1]
    return content or [w for w in ws if len(w) > 1]


def index(phrases):
    """Look-up tables for search(): built once per page (or per server call)."""
    en_post: dict = {}
    fr_post: dict = {}
    for pi, p in enumerate(phrases):
        en = p.get("en") or {}
        parts = norm(" || ".join([en.get(k) or "" for k in tones.KEYS])).split("||")
        for k, part in zip(tones.KEYS, parts):
            for w in part.split():
                if len(w) < 2:
                    continue
                post = en_post.setdefault(w, {})
                post.setdefault(pi, set()).add(k)
        fr = p.get("fr") or {}
        for w in norm(" ".join([fr.get(k) or "" for k in tones.KEYS])).split():
            if len(w) >= 2:
                fr_post.setdefault(w, set()).add(pi)
    return {"en": en_post, "fr": fr_post, "en_by": _buckets(en_post), "fr_by": _buckets(fr_post),
            "en_lines": [[norm(en_text) for en_text in (p.get("en") or {}).values() if en_text] for p in phrases]}


def _buckets(post):
    out: dict = {}
    for w in post:
        out.setdefault(w[:2], []).append(w)
    return out


def _alts(term):
    alts = [(term, 1.0)]
    if len(term) > 4 and term.endswith("s"):
        alts.append((term[:-1], 1.0))
    for a in GROUP.get(term, []):
        if a != term:
            alts.append((a, 0.5))
    return alts


def _hits(buckets, term):
    """{indexed word: weight} for every word this search term (or a synonym of it) matches."""
    out: dict = {}
    for alt, weight in _alts(term):
        for w in buckets.get(alt[:2], []):
            if w == alt or (len(alt) >= 3 and w.startswith(alt)):
                if weight > out.get(w, 0):
                    out[w] = weight
    return out


def search(idx, phrases, query, mood="Basic", limit=20):
    """{"items": [phrase, ...] best first (at most `limit`, None = all), "total": matches, "terms": [...]}."""
    ts = terms(query)
    if not ts:
        return {"items": [], "total": 0, "terms": []}
    strong = ("Basic", mood)
    totals: dict = {}
    for term in ts:
        per: dict = {}
        for w, weight in _hits(idx["en_by"], term).items():
            for pi, moods in idx["en"][w].items():
                s = 0
                for k in moods:
                    s += 2 if k in strong else 1
                if s * weight > per.get(pi, 0):
                    per[pi] = s * weight
        fr_seen: dict = {}
        for w, weight in _hits(idx["fr_by"], term).items():
            for pi in idx["fr"][w]:
                if 2 * weight > fr_seen.get(pi, 0):
                    fr_seen[pi] = 2 * weight
        for pi, s in fr_seen.items():
            per[pi] = per.get(pi, 0) + s
        for pi, s in per.items():
            got = totals.setdefault(pi, [0, 0.0])
            got[0] += 1
            got[1] += s
    whole = " ".join(words(query))
    ranked = []
    for pi in totals:
        got = totals[pi]
        bonus = 0
        if len(whole.split()) >= 2:
            for line in idx["en_lines"][pi]:
                if whole in line:
                    bonus = 6
        ranked.append((-got[0], -(got[1] + bonus), phrases[pi].get("id") or 0, pi))
    ranked.sort()  # no lambdas here: the browser's Python (Skulpt) mishandles closures over these locals
    items = [phrases[row[3]] for row in ranked]
    return {"items": items if limit is None else items[:limit], "total": len(items), "terms": ts}


def suggestions(idx, n=8):
    """Up to n search words that always find something: the everyday situations first, then the library's most
    common words. Returns [(chip text, search text)]."""
    out, seen = [], set()
    for w in CURATED:
        if len(out) >= n:
            break
        if _hits(idx["en_by"], w):
            out.append((CHIP_TEXT.get(w, w), CHIP_TEXT.get(w, w)))
            seen.add(w)
    if len(out) < n:
        common = sorted([(-len(post), w) for w, post in idx["en"].items()
                         if len(w) >= 4 and w not in STOP and w not in LISTENERS and w not in seen])
        for neg, w in common:
            if len(out) >= n:
                break
            out.append((w, w))
    return out
