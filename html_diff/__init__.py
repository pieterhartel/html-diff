# HTML-Diff
#
# Copyright (C) 2019 Quentin Wenger
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


__version__ = "0.3.0"

import difflib
import re

import bs4

from .config import Config
from .config import config



class Cache(dict):
    pass


class Match:
    @property
    def matching_length(self):
        raise NotImplementedError
    def dump_to_tag_list(self, soup):
        raise NotImplementedError


def iter_cut_words(s):
    for x in re.split(r"(\W)", s):
        if x:
            yield x


class StringLeafMatch(Match):
    def __init__(self, a, b):
        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
            self.a = list(iter_cut_words(a))
            self.b = list(iter_cut_words(b))
        else:
            self.a = a
            self.b = b
        self.sm = difflib.SequenceMatcher(a=self.a, b=self.b)
    @property
    def matching_length(self):
        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
            return sum(len(x) for b in self.sm.get_matching_blocks() for x in self.a[b.a:b.a + b.size])
        else:
            return sum(b.size for b in self.sm.get_matching_blocks())
    def dump_to_tag_list(self, soup):
        if self.a == self.b:
            if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
                return ["".join(self.a)]
            else:
                return [self.a]
        else:
            tags = []
            if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_PRECISE:
                if self.a:
                    tag = soup.new_tag("del")
                    tag.append(self.a)
                    tags.append(tag)
                if self.b:
                    tag = soup.new_tag("ins")
                    tag.append(self.b)
                    tags.append(tag)
                return tags
            else:
                for opcode, i1, i2, j1, j2 in self.sm.get_opcodes():
                    if opcode == "equal":
                        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
                            tags.append("".join(self.a[i1:i2]))
                        else:
                            tags.append(self.a[i1:i2])
                    if opcode in ("delete", "replace"):
                        tag = soup.new_tag("del")
                        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
                            tag.append("".join(self.a[i1:i2]))
                        else:
                            tag.append(self.a[i1:i2])
                        tags.append(tag)
                    if opcode in ("insert", "replace"):
                        tag = soup.new_tag("ins")
                        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_SIMPLE:
                            tag.append("".join(self.b[j1:j2]))
                        else:
                            tag.append(self.b[j1:j2])
                        tags.append(tag)
            return tags


class BlockLeafMatch(Match):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    @property
    def matching_length(self):
        if self.a == self.b:
            if self.a.is_empty_element:
                return len(str(self.a))
            else:
                return len(self.a.string)
        return 0
    def dump_to_tag_list(self, soup):
        if self.a == self.b:
            return [self.a]
        else:
            tags = []
            if self.a:
                tag = soup.new_tag("del")
                tag.append(self.a)
                tags.append(tag)
            if self.b:
                tag = soup.new_tag("ins")
                tag.append(self.b)
                tags.append(tag)
            return tags


class NoLeafMatch(Match):
    def __init__(self, a_s, b_s):
        self.a_s = a_s
        self.b_s = b_s
    @property
    def matching_length(self):
        return 0
    def dump_to_tag_list(self, soup):
        tags = []
        if self.a_s:
            tag = soup.new_tag("del")
            tag.extend(self.a_s)
            tags.append(tag)
        if self.b_s:
            tag = soup.new_tag("ins")
            tag.extend(self.b_s)
            tags.append(tag)
        return tags


class TreeMatch(Match):
    def __init__(self, child, match_before=None, match_after=None, reference_tag=None):
        self.child = child
        self.match_before = match_before
        self.match_after = match_after
        self.reference_tag = reference_tag
    @property
    def matching_length(self):
        return (
            self.child.matching_length
            + (0 if self.match_before is None else self.match_before.matching_length)
            + (0 if self.match_after is None else self.match_after.matching_length)
        )
    @staticmethod
    def ensure_cache(cache, key, value_fct):
        if key in cache:
            value = cache[key]
        else:
            value = value_fct()
            cache[key] = value
        return value
    @staticmethod
    def cut_words(children):
        if config.cuttable_words_mode == Config.CuttableWordsMode.UNCUTTABLE_PRECISE:
            for child in children:
                if isinstance(child, (bs4.element.NavigableString, str)):
                    yield from iter_cut_words(child)
                else:
                    yield child
        else:
            yield from children
    @classmethod
    def from_children_cached(cls, a_children, b_children, cache, reference_tag=None):
        a_children = tuple(cls.cut_words(a_children))
        b_children = tuple(cls.cut_words(b_children))
        key = (a_children, b_children, reference_tag)
        return cls.ensure_cache(cache, key, lambda: cls.from_children(a_children, b_children, cache, reference_tag))
    @classmethod
    def from_children(cls, a_children, b_children, cache, reference_tag=None):
        best_match = (None, None, None)
        for a_index, a_child in enumerate(a_children):
            for b_index, b_child in enumerate(b_children):
                match = None
                if (
                    isinstance(a_child, (bs4.element.NavigableString, str))
                    and isinstance(b_child, (bs4.element.NavigableString, str))
                ):
                    match = cls.ensure_cache(cache, (a_child, b_child), lambda: StringLeafMatch(a_child, b_child))
                elif (
                    isinstance(a_child, bs4.element.Tag)
                    and isinstance(b_child, bs4.element.Tag)
                    and a_child.name == b_child.name
                    and a_child.attrs == b_child.attrs
                ):
                    if any(fct(a_child) for fct in config.tags_fcts_as_blocks):
                        match = cls.ensure_cache(cache, (a_child, b_child), lambda: BlockLeafMatch(a_child, b_child))
                    else:
                        match = cls.from_children_cached(a_child.children, b_child.children, cache, a_child)
                if (
                    match is not None
                    and (best_match[0] is None or best_match[0].matching_length < match.matching_length)
                ):
                    best_match = (match, a_index, b_index)
        if best_match[0] is None:
            return cls(
                cls.ensure_cache(cache, (a_children, b_children), lambda: NoLeafMatch(a_children, b_children)),
                reference_tag=reference_tag,
            )
        else:
            match_before = None
            match_after = None
            if best_match[1] > 0 or best_match[2] > 0:
                match_before = cls.from_children_cached(a_children[:best_match[1]], b_children[:best_match[2]], cache)
            if best_match[1] + 1 < len(a_children) or best_match[2] + 1 < len(b_children):
                match_after = cls.from_children_cached(a_children[best_match[1] + 1:], b_children[best_match[2] + 1:], cache)
            return cls(best_match[0], match_before, match_after, reference_tag)
    def dump_to_tag_list(self, soup):
        tags = []
        if self.match_before is not None:
            tags.extend(self.match_before.dump_to_tag_list(soup))
        tags.extend(self.child.dump_to_tag_list(soup))
        if self.match_after is not None:
            tags.extend(self.match_after.dump_to_tag_list(soup))
        if self.reference_tag is None:
            return tags
        else:
            tag = soup.new_tag(self.reference_tag.name, attrs=self.reference_tag.attrs)
            tag.extend(tags)
            return [tag]


def diff(a, b):
    # NOTE: use the builtin parser to parse as a snippet, without <html> tags, etc.
    a_soup = bs4.BeautifulSoup(a, "html.parser")
    b_soup = bs4.BeautifulSoup(b, "html.parser")
    c_soup = bs4.BeautifulSoup("", "html.parser")
    c_soup.extend(TreeMatch.from_children_cached(a_soup.children, b_soup.children, Cache()).dump_to_tag_list(c_soup))
    return str(c_soup)

