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


from enum import Enum



class Config:
    class CuttableWordsMode(Enum):
        CUTTABLE = 0
        UNCUTTABLE_SIMPLE = 1
        UNCUTTABLE_PRECISE = 2


config = Config()

config.tags_fcts_as_blocks = [
    lambda tag: tag.is_empty_element,
]

config.cuttable_words_mode = Config.CuttableWordsMode.CUTTABLE

