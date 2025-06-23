# -*- coding: UTF-8 -*-
# Copyright (C) 2025 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from datetime import datetime
from operator import iadd
import codecs
import io
import os
import re
import sys

from dictionary import *

try: reduce
except: from functools import reduce

try: unichr
except: unichr = chr

DEFAULT_ZH_TW_TABLE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "addon", "brailleTables", "zh-tw.ctb"))
DEFAULT_YAML_TEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "zh-tw-dictionary.yaml"))

p2h = lambda x, i=0: ("_%d"%(i%len(x),) if i != 0 else "") + ('"%s"'%(s2h(x[:i]),) if x[:i] else "") + ('["%s"]' if len(x) > 1 else '"%s"')%(s2h(x[i]),) + ('"%s"'%(s2h(x[i+1:]),) if x[i+1:] else "")

CHI = reduce(iadd, (list(range(*t)) for t in [
    (0x2E80, 0x2FE0), # CJK Radicals Supplement
    (0x3007, 0x3008), # CJK Symbols and Punctuation
    (0x3400, 0xA000), # CJK Unified Ideographs Extension A, CJK Unified Ideographs
    (0xF900, 0xFB00), # CJK Compatibility Ideographs
]))

class LouisBRLTBL:
    def __init__(self, table_path):
        self.table_path = table_path
        self.tbl, self.word = {}, {}
        with codecs.open(table_path, encoding="UTF-8-SIG") as tblf:
            self.tbl_txt = [] # The original text of the table.
            self.han_rules_begin = -1 # The insertion index of Han character rules.
            for l in tblf:
                l = re.sub(r"[\n\r]+$", "", l) # Clear newline characters.
                if self.han_rules_begin < len(self.tbl_txt):
                    self.tbl_txt.append(l)
                if re.match(r"^\s*\#begin\s*Han\s*character\s*rules\b", l):
                    if self.han_rules_begin >= 0: raise SyntexError("Duplicate Han character rules section.")
                    self.han_rules_begin = len(self.tbl_txt)
                elif re.match(r"^\s*\#end\s*Han\s*character\s*rules\b", l):
                    if self.han_rules_begin < 0: raise SyntexError("No beginning of Han character rules section.")
                    self.tbl_txt.append(l)
                l = l.strip()
                if not l or l[0] == '#': continue
                l = re.split("\\s+", l, re.U)
                if l[0] in ("attribute", "begword", "include", "noback"): continue
                if l[0] == "word": # The word command.
                    self.word[h2s(l[1])] = l[2]
                else: # The ordinary character definition.
                    self.tbl[h2s(l[1])] = l[2]
        self.p2b, self.w2p = {}, {}
    def make_rules(self, data):
        for phrase in data["phrases"]: # Construct p2b and w2p.
            for t in phrase:
                try: # Collect phrases containing character t.
                    self.w2p[t][0].add(phrase)
                except KeyError: # The initial element of a self.w2p entry.
                    self.w2p[t] = [{phrase}, False]
            self.p2b[phrase] = [[], []]
            self.p2b[phrase][0] = data["phrases"][phrase]
            self.p2b[phrase][1] = list((b != a) for b, a in zip(data["phrases"][phrase], (self.tbl[t] for t in phrase)))
        for p in self.p2b:
            for w in (t[0] for t in zip(p, self.p2b[p][1]) if t[1]):
                self.w2p[w][1] = True # Occurrence of heteronym with a different pronunciation.
        for p in sorted(self.p2b.keys(), key=len):
            if len(p) > 2: # A long phrase p.
                # Some heteronyms have different pronunciations in a long phrase p and a short phrase q, where q is a
                # substring of p. The heteronym p[i] must be marked even if its pronunciation is the same as the default.
                for i in filter(lambda i: not self.p2b[p][1][i], range(len(p))): # p[i]: A word not marked as heteronym.
                    for q in sorted(self.w2p[p[i]][0] - {p}): # q: A phrase, but p, containing p[i].
                        for j in (m.start() for m in re.finditer(q, p) if i in range(m.start(), m.end())):
                            self.p2b[p][1][i] = self.p2b[p][1][i] or self.p2b[q][1][i - j]
            if not sum(self.p2b[p][1]) and not any(t in data["variants"] for t in p): raise ValueError("No heteronym: {0}".format(p))
            if len(p) <= 2: continue
            # Place heteronym marks at the beginning and the end of a long phase according to self.w2p.
            for i in (0, -1): # The head and the tail.
                self.p2b[p][1][i] = self.p2b[p][1][i] or self.w2p[p[i]][1]
        memory_file = io.StringIO()
        for w in sorted(data["variants"].keys(), key=lambda x: (-len(x), x)):
            if len(w) > 1: # Conditional replacement (usually for simplified words).
                # The "noback correct" rule for w[i] is additional and necessary.
                for i in (j for j in range(len(w)) if data["variants"][w][j] not in (w[j], data["variants"].get(w[j], w[j]))):
                    print("noback correct", p2h(w, i), p2h(data["variants"][w][i]), file=memory_file)
                continue
            if w in self.w2p: # Invariant cases for "noback correct".
                # By default, each occurrence of variants should be replaced with their corresponding canonical
                # words. However, phrases in data["phrases"] must remain unchanged for correct application of
                # "noback context" rules.
                for x in sorted(self.w2p[w][0]): # For each phrase x containing w.
                    for y in re.finditer(w, x):
                        print("noback correct", p2h(x, y.start()), p2h(w), file=memory_file)
            print("noback correct", p2h(w), p2h(data["variants"][w]), file=memory_file) # The default replacement rule.
        for p in sorted(self.p2b.keys(), key=lambda x: (-len(x), x)):
            if sum(self.p2b[p][1]):
                print("\n#", s2h(p), "-".join(self.p2b[p][0]), file=memory_file)
            for i in range(len(p)):
                if self.p2b[p][1][i]: # The occurrence of heteronym.
                    print("noback context", p2h(p, i), "@" + self.p2b[p][0][i], file=memory_file)
        with io.open(self.table_path, "w", encoding="UTF-8", newline=os.linesep) as tblf:
            state = 0 # It determines the next detected syntax.
            for line in self.tbl_txt[:self.han_rules_begin]:
                if state == 0: # Detect the copyright declaration.
                    m = re.match(r"\s*\#\s*Copyright\s*\(C\)\s*\d{4}-(\d{4})\s*nvda-tw\b", line)
                    if m:
                        line = "{0}{1}{2}".format(line[:m.start(1)], datetime.today().year, line[m.end(1):])
                        state = 1
                elif state == 1: # Detect the version declaration.
                    m = re.match(r"\s*\#\s*Version\s*:\s*(\d+(?:-\d+)*)\b", line)
                    if m:
                        line = line[:m.start(1)] + datetime.today().strftime("%Y-%m") + line[m.end(1):]
                        state = 2
                print(line, file=tblf)
            tblf.write(memory_file.getvalue()) # newline conversion also works here.
            for line in self.tbl_txt[self.han_rules_begin:]:
                print(line, file=tblf)
    def make_tests(self, data, yaml_path):
        with io.open(yaml_path, "w", encoding="UTF-8", newline=os.linesep) as ymlf:
            print(u"# Copyright \u00A9 2022 Bo-Cheng Jhan <school510587@yahoo.com.tw>", file=ymlf)
            print(u"# Copyright \u00A9 2022-{0} nvda-tw <https://groups.io/g/nvda-tw>".format(datetime.today().year), file=ymlf)
            print("#", file=ymlf)
            print("# This file is part of liblouis.", file=ymlf)
            print("#", file=ymlf)
            print("# Copying and distribution of this file, with or without modification,", file=ymlf)
            print("# are permitted in any medium without royalty provided the copyright", file=ymlf)
            print("# notice and this notice are preserved.  This file is offered as-is,", file=ymlf)
            print("# without any warranty.", file=ymlf)
            print("#", file=ymlf)
            print("# Currently maintained by Sponge Jhan <school510587@yahoo.com.tw>", file=ymlf)
            print("# Version:", datetime.today().strftime("%Y-%m"), file=ymlf)
            print("", file=ymlf)
            print("# This file is dedicated for Han character test cases. The following tests", file=ymlf)
            print("# are generated from some dictionary file(s) automatically.", file=ymlf)
            print("", file=ymlf)
            print("# The display tables have been separated from the translation tables. But in", file=ymlf)
            print("# the case of this test some display relevant stuff is still defined in the", file=ymlf)
            print("# translation table. That is why we have to include it here.", file=ymlf)
            print("display: unicode.dis", file=ymlf)
            print("table:", file=ymlf)
            print("  language: cmn", file=ymlf)
            print("  region: cmn-TW", file=ymlf)
            print("  __assert-match: zh-tw.ctb", file=ymlf)
            print("flags: {testmode: forward}", file=ymlf)
            print("tests:", file=ymlf)
            for c in sorted(set(data["variants"].keys()) | set(self.word.keys())):
                try:
                    if len(c) == 1:
                        p = self.word.get(data["variants"][c], self.tbl[data["variants"][c]]) if c in data["variants"] else self.word[c]
                        if p != self.tbl[c]:
                            print_test(c, p, ymlf)
                except KeyError: pass
            for p in sorted(self.p2b.keys()):
                print_test(p, self.p2b[p][0], ymlf)

data = load_dictionary(DEFAULT_JSON_PATH)
add_missing_variants(data["variants"])
brltbl = LouisBRLTBL(DEFAULT_ZH_TW_TABLE_PATH)
brltbl.make_rules(data)
brltbl.make_tests(data, os.path.join(DEFAULT_YAML_TEST_PATH))
