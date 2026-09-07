"""SY Design Studio Ltd's own practice profile — the in-house documents only.

This is NOT the default. docgen/practice.py reads a profile and hard-codes none, because a
generated document carries the subscribing practice's identity and never the vendor's. This
file is one profile among others, reached only by asking for it: --practice brand.
"""

PRACTICE = {
    "name":    "SY Design Studio Ltd",
    "designer":"Salman Yousaf",
    "addr":    "49 Durham Avenue, Hounslow, TW5 0HG",
    "email":   "info@specline.co.uk",
    "accent":  "F5900A",
    "logo":    "sy_logo.png",
    "web":     "www.sydesignstudio.co.uk",
}

import os
PRACTICE["logo"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), PRACTICE["logo"])
