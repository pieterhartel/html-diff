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


import re



def new_from_diff(diff):
    return re.sub("<ins>(.*?)</ins>", r"\1", re.sub("<del>.*?</del>", "", diff))


def old_from_diff(diff):
    return re.sub("<del>(.*?)</del>", r"\1", re.sub("<ins>.*?</ins>", "", diff))


def is_diff_valid(old, new, diff):
    return old == old_from_diff(diff) and new == new_from_diff(diff)

