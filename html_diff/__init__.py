# HTML-Diff
#
# Copyright (C) 2019-2021 Quentin Wenger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


__version__ = "0.4.1"

import re

import bs4

from .config import config



class NodeString:
    def __init__(self, ai):
        self.ai = ai
        self.s = len(self.ai)
    def dump_to_tag_list(self, soup):
        return [self.ai]


pattern = re.compile(r"(\W)")

def split_contents_iter(contents):
    for content in contents:
        if isinstance(content, bs4.element.NavigableString):
            for x in pattern.split(content):
                if x:
                    yield x
        else:
            yield content

def split_contents(contents):
    return list(split_contents_iter(contents))


class NodeOtherTag:
    def __init__(self, ai, bi, main=False):
        self.ai = ai
        self.main = main
        ac = split_contents(ai.contents)
        bc = split_contents(bi.contents)
        self.node = Node(ac, bc, 0, 0, len(ac), len(bc))
        self.s = self.node.s + config.OTHER_ELEMENT_SCORE
    def dump_to_tag_list(self, soup):
        if self.main:
            return self.node.dump_to_tag_list(soup)
        else:
            tag = soup.new_tag(self.ai.name, attrs=self.ai.attrs)
            tag.extend(self.node.dump_to_tag_list(soup))
            return [tag]


class NodeBlockTag:
    def __init__(self, ai, bi):
        self.ai = ai
        self.bi = bi
        if ai.is_empty_element:
            self.s = config.EMPTY_ELEMENT_SCORE
        elif ai.string == bi.string:
            self.s = len(ai.string) + config.OTHER_ELEMENT_SCORE
        else:
            self.s = config.OTHER_ELEMENT_SCORE
    def dump_to_tag_list(self, soup):
        if self.ai.is_empty_element:
            return [self.ai]
        else:
            if self.ai.string == self.bi.string:
                return [self.ai]
            else:
                dtag = soup.new_tag("del")
                dtag.append(self.ai)
                itag = soup.new_tag("ins")
                itag.append(self.bi)
                return [dtag, itag]


c = {}

def cache(fct):
    def f(*args):
        if args in c:
            return c[args]
        else:
            r = fct(*args)
            c[args] = r
            return r
    return f

def clear_cache():
    c.clear()


@cache
def node_element(ai, bi):
    if isinstance(ai, str) and isinstance(bi, str):
        if ai == bi:
            return NodeString(ai)
    elif isinstance(ai, bs4.element.Tag) and isinstance(bi, bs4.element.Tag):
        if ai.name == bi.name and ai.attrs == bi.attrs:
            if any(fct(ai) for fct in config.tags_fcts_as_blocks):
                return NodeBlockTag(ai, bi)
            else:
                return NodeOtherTag(ai, bi)
    return None


def best_matching_range(a, b, al, bl, ar, br):
    max_score = (al, bl, [], 0)
    for ai in range(al, ar):
        for bi in range(bl, br):
            s = 0
            ns = []
            for aj, bj in zip(range(ai, ar), range(bi, br)):
                n = node_element(a[aj], b[bj])
                if n is None:
                    break
                else:
                    s += n.s
                    ns.append(n)
            if s != 0 and s > max_score[3]:
                max_score = (ai, bi, ns, s)
    if max_score[3]:
        return Range(a, b, *max_score)
    else:
        return None


class Range:
    def __init__(self, a, b, al, bl, ns, s):
        self.a = a
        self.b = b
        self.al = al
        self.bl = bl
        self.ar = al + len(ns)
        self.br = bl + len(ns)
        self.ns = ns
        self.s = s
    def dump_to_tag_list(self, soup):
        return [t for n in self.ns for t in n.dump_to_tag_list(soup)]


class NodeNoMatch:
    def __init__(self, a, b, al, bl, ar, br):
        self.a = a
        self.b = b
        self.al = al
        self.bl = bl
        self.ar = ar
        self.br = br
        self.s = 0
    def dump_to_tag_list(self, soup):
        tags = []
        if self.ar > self.al:
            tag = soup.new_tag("del")
            tag.extend(self.a[self.al:self.ar])
            tags.append(tag)
        if self.br > self.bl:
            tag = soup.new_tag("ins")
            tag.extend(self.b[self.bl:self.br])
            tags.append(tag)
        return tags


class Node:
    def __init__(self, a, b, al, bl, ar, br):
        self.a = a
        self.b = b
        self.al = al
        self.bl = bl
        self.ar = ar
        self.br = br
        self.range = best_matching_range(a, b, al, bl, ar, br)
        self.node_left = None
        self.node_right = None
        if not self.range:
            self.node_left = NodeNoMatch(a, b, al, bl, ar, br)
        else:
            if self.range.al > al or self.range.bl > bl:
                self.node_left = Node(a, b, al, bl, self.range.al, self.range.bl)
            if self.range.ar < ar or self.range.br < br:
                self.node_right = Node(a, b, self.range.ar, self.range.br, ar, br)
        self.s = sum(k.s for k in (self.node_left, self.range, self.node_right) if k is not None)
    def dump_to_tag_list(self, soup):
        return sum((k.dump_to_tag_list(soup) for k in (self.node_left, self.range, self.node_right) if k is not None), [])


def diff(a, b):
    # NOTE: use the builtin parser to parse as a snippet, without <html> tags, etc.
    a_soup = bs4.BeautifulSoup(a, "html.parser")
    b_soup = bs4.BeautifulSoup(b, "html.parser")
    c_soup = bs4.BeautifulSoup("", "html.parser")
    c_soup.extend(NodeOtherTag(a_soup, b_soup, True).dump_to_tag_list(c_soup))
    return str(c_soup)
