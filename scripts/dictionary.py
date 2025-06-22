# -*- coding: UTF-8 -*-
# Copyright (C) 2025 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from operator import concat, countOf, ior
import codecs
import io
import json
import os
import re
import sys
import unicodedata

try: reduce
except: from functools import reduce

try: unichr
except: unichr = chr

DEFAULT_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "zh-tw-dictionary.json"))

h2s = lambda x: re.sub(r"(?i)\\([ux][0-9A-Z]{4}|y[0-9A-Z]{5}|z[0-9A-Z]{8})", lambda m: unichr(int(m.group(1)[1:], 16)), x)
s2h = lambda x: "".join(c if ord(c) < 128 else (("\\x%04X" if ord(c) < 0x10000 else "\\y%05X" if ord(c) < 0x100000 else "\\z08X") % (ord(c),)) for c in x)

def add_missing_variants(data_variants):
    for c in map(unichr, range(0xF900, 0xFB00)):
        x = unicodedata.normalize("NFKD", c)
        if ord(x) < 0x10000 and x != c and c not in data_variants:
            data_variants[c] = data_variants.get(x, x)

def fix_indirect_variants(data_variants):
    for word in data_variants: # Warning when (k, l) and (l, m) coexists.
        path = [word] # To explore a path beginning from the word.
        while data_variants[word] not in path:
            path.append(data_variants[word])
            if data_variants[word] not in data_variants: # The path ends.
                break
            data_variants[word] = data_variants[data_variants[word]] # The next node on the path.
        else: # A cycle (loop) is detected.
            raise SyntaxError(" -> ".join(path[path.find(data_variants[word]):] + [data_variants[word]]))
        if len(path) > 2: # A long path is detected.
            print("Warning:", " -> ".join(path), file=sys.stderr)

def load_dictionary(json_path):
    with codecs.open(json_path, encoding="UTF-8-SIG") as json_file:
        json_content = json_file.read()
        data = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(json_content)
        for phrase, dot_pattern in data["phrases"].items():
            if len(phrase) != len(dot_pattern):
                raise ValueError("Inconsistent {0} => {1}".format(phrase, dot_pattern))
            for i, cells in enumerate(dot_pattern):
                for j, cell in enumerate(cells.split("-")):
                    if len(cell) < 1:
                        raise ValueError("Empty cell in character {0} cell {1} of phrase {2}".format(i, j, phrase))
                    if not re.match("^0|1?2?3?4?5?6?7?8?$", cell):
                        raise ValueError("Format error in character {0} cell {1} of phrase {2}".format(i, j, phrase))
        for k, v in data["variants"].items():
            if len(k) != len(v):
                raise ValueError("Different length: {0} {1}".format(k, v))
        return data

brl = lambda p: "".join(unichr(0x2800 | (0 if x == '0' else reduce(ior, (1 << (ord(d) - ord('1')) for d in x)))) for x in "-".join(p).split("-"))
def print_test(case, answer, ymlf):
    if len(case) < 2: # Single-letter case.
        print('  - ["%s", "%s"]'%(case, brl((answer,))), file=ymlf)
    else: # Multiple-letter case.
        print('  - - "{0}"'.format(case), file=ymlf)
        print('    - "{0}"'.format(brl(answer)), file=ymlf)
        print("    - outputPos:", "[0" + (", %d" * (len(case) - 1)) % tuple((countOf("-".join(answer[:i]), "-") + 1) for i in range(1, len(case))) + "]", file=ymlf)
        print("      inputPos:", reduce(concat, ([i] * (countOf(answer[i], "-") + 1) for i in range(len(case)))), file=ymlf)

if __name__ == "__main__":
    print("Usage:", sys.argv[0], "[<path/to/zh-tw-dictionary.json>]", file=sys.stderr)
    print("The destination with sorted keys:", DEFAULT_JSON_PATH, file=sys.stderr)
    print("If the argument is not specified, in-place modification will occur in the default JSON dictionary.", file=sys.stderr)
    try:
        source_json_path = sys.argv[1]
        if len(sys.argv) > 2:
            exit(1)
    except IndexError:
        source_json_path = DEFAULT_JSON_PATH
    data = load_dictionary(source_json_path)
    with io.open(DEFAULT_JSON_PATH, "w", encoding="UTF-8", newline=os.linesep) as json_file:
        print(json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True), file=json_file)
