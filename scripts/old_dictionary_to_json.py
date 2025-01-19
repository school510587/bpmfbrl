# -*- coding: UTF-8 -*-
# Copyright (C) 2025 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
import codecs
import json
import os
import re
import sys

try: reduce
except: from functools import reduce

try: unichr
except: unichr = chr

h2s = lambda x: re.sub(r"(?i)\\([ux][0-9A-Z]{4}|y[0-9A-Z]{5}|z[0-9A-Z]{8})", lambda m: unichr(int(m.group(1)[1:], 16)), x)
s2h = lambda x: "".join(c if ord(c) < 128 else (("\\x%04X" if ord(c) < 0x10000 else "\\y%05X" if ord(c) < 0x100000 else "\\z08X") % (ord(c),)) for c in x)

if len(sys.argv) < 2:
    print("Usage:", sys.argv[0], "<path/to/zh-tw.ctb>", file=sys.stderr)
    exit()

tbl, word = {}, {}
with codecs.open(sys.argv[1], encoding="UTF-8") as tblf:
    for l in tblf:
        l = l.strip()
        if not l or l[0] == '#': continue
        l = l.split(" ")
        if l[0] in ("begword", "include", "noback") or len(l[1]) > 6: continue
        if l[0] == "word":
            word[h2s(l[1])] = l[2]
        else:
            tbl[h2s(l[1])] = l[2]

data = {}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
with codecs.open(os.path.join(DATA_DIR, "zh-tw.dict.txt"), encoding="UTF-8") as phdict:
    count, error = 0, 0
    for l in phdict:
        count += 1
        l = l.strip()
        if l[0] == '#':
            print(l)
            continue
        x = l.split(" ")
        text = h2s(x[1])
        print("Phrase:", text, file=sys.stderr)
        if len(text) < 2:
            print("Error:", "Not a phrase.", file=sys.stderr)
            continue
        elif text in data:
            print("Error:", "Duplicate items of the same phrase.", file=sys.stderr)
            continue
        data[text] = x[2].split("-9-")
        if len(data[text]) != len(text):
            if len(data[text]) != 1:
                print("Error:", "# of characters != # of patterns separated by 9.", file=sys.stderr)
                continue
            elif len(text) > 2:
                print("Error:", "9 is required for a long phrase.", file=sys.stderr)
                continue
            elif text[0] not in tbl and text[0] not in word:
                print("Error:", "9 is required for a phrase without the first known pattern.", file=sys.stderr)
                continue
            data[text] = data[text][0].split("-")
            default_pattern = tbl[text[0]].split("-")
            if data[text][:len(default_pattern)] == default_pattern:
                data[text] = ["-".join(default_pattern), "-".join(data[text][len(default_pattern):])]
                continue
            if text[1] not in tbl and text[1] not in word:
                print("Error:", "9 is required for a phrase without the second known pattern.", file=sys.stderr)
                continue
            default_pattern = tbl[text[1]].split("-")
            if data[text][-len(default_pattern):] == default_pattern:
                data[text] = ["-".join(data[text][:-len(default_pattern)]), "-".join(default_pattern)]
                continue
            print("Error:", "No proper rule to parse the item.", file=sys.stderr)
            error += 1
    print("Total:", count, file=sys.stderr)
    print("Error:", error, file=sys.stderr)

print(json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True))
