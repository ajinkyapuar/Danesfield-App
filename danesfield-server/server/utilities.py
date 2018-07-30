#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##############################################################################

import re


def removeDuplicateCount(name):
    """
    Remove duplicate count suffix from a name.
    For example, 'my_file (1).txt' becomes 'my_file.txt'.
    """
    return re.sub(r' \(\d+\)$', '', name)


def hasExtension(item, extension):
    """
    Return true if the item's name has the specified extension.
    Ignores duplicate count suffixes.

    :param item: Item document.
    :type item: dict
    :param extension: The file extension, including a leading period.
    :type extension: str
    """
    return removeDuplicateCount(item['name']).lower().endswith(extension)