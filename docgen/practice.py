"""Whose name goes on a generated document — the practice USING the tool.

One lookup, shared by every generator, so the Word specification, the PDF and the detail
sheets cannot disagree about who drew them.

THE RULE THIS EXISTS FOR. A specification or a detail carries the subscribing practice's own
identity and never the vendor's. No technologist will issue a drawing to building control under
another company's name, and a document that arrives with someone else's practice on the cover
is worse than one with a blank. So nothing here is hard-coded: the details are read, and with
none found the documents print placeholders for a practice to fill in. A blank cover gets
corrected before issue; another firm's name might not.

WHERE IT LOOKS, first hit wins:
    an explicit path passed by the caller
    the SPECLINE_PRACTICE environment variable
    specline-practice.json in the directory ABOVE the repository, where a per-installation
        file cannot be committed or shipped
    "brand" as the path, meaning docgen/brand_inhouse.py, for SY Design Studio's own documents

In the hosted app the same details come from the `practices` row for the signed-in account,
which is where a document generated server-side takes them from.

A profile is JSON:

    {"name": "...", "designer": "...", "addr": "...", "email": "...", "web": "...",
     "accent": "#RRGGBB", "logo": "relative/or/absolute/path.png"}

`accent` and `logo` are the practice's own branding on its own documents. Both are optional;
without them a document is set in a neutral dark grey with the practice name as a wordmark.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ("name", "designer", "addr", "email", "web", "accent", "logo")
NEUTRAL_ACCENT = "3E4244"          # the same dark grey the body text uses


def load(source=None):
    p, where = {}, "placeholders"

    if source == "brand":
        try:
            import importlib
            m = importlib.import_module("brand_inhouse")
            p, where = dict(m.PRACTICE), "docgen/brand_inhouse.py"
        except Exception as e:
            print("  could not read the in-house profile (%s)" % e)
    else:
        path = (source or os.environ.get("SPECLINE_PRACTICE")
                or os.path.join(os.path.dirname(ROOT), "specline-practice.json"))
        if path and os.path.isfile(path):
            try:
                p = json.load(open(path, encoding="utf-8"))
                where = path
            except Exception as e:
                print("  could not read %s (%s)" % (path, e))
            if p.get("logo") and not os.path.isabs(p["logo"]):
                p["logo"] = os.path.normpath(os.path.join(os.path.dirname(path), p["logo"]))

    out = {k: str(p.get(k, "")).strip() for k in FIELDS}
    out["source"] = where
    out["name"] = out["name"] or "[Practice name]"
    out["accent"] = (re.sub(r"[^0-9A-Fa-f]", "", out["accent"]) or NEUTRAL_ACCENT)[:6].upper()
    if len(out["accent"]) != 6:
        out["accent"] = NEUTRAL_ACCENT
    if out["logo"] and not os.path.isfile(out["logo"]):
        out["logo"] = ""

    parts = [w for w in re.split(r"[\s-]+", out["designer"]) if w]
    out["initials"] = "".join(w[0] for w in parts[:3]).upper() or "[XX]"
    out["who"] = ("%s of %s" % (out["designer"], out["name"])) if out["designer"] \
                 else "The named designer"
    return out


def describe(p):
    return "%s%s  (from %s)" % (p["name"],
                                " / " + p["designer"] if p["designer"] else "",
                                p["source"])
