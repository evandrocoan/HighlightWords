#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################### Licensing #######################################################
#
#   Copyright 2018 @ Evandro Coan
#   Project Unit Tests
#
#  Redistributions of source code must retain the above
#  copyright notice, this list of conditions and the
#  following disclaimer.
#
#  Redistributions in binary form must reproduce the above
#  copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials
#  provided with the distribution.
#
#  Neither the name Evandro Coan nor the names of any
#  contributors may be used to endorse or promote products
#  derived from this software without specific prior written
#  permission.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################################
#

import sublime_plugin

import re
import os
import sys

import unittest

from debug_tools import utilities
from debug_tools import testing_utilities

# sublime_plugin.reload_plugin( "debug_tools.testing_utilities" )
from HighlightWords import HighlightWords


class PushdownUnitTests(testing_utilities.TestingUtilities):

    def test_searchAndWord(self):
        expression = "/var/ /var/ a kljafçl sadjfoiajuf / /"
        tree = HighlightWords._parser.parse( expression )

        self.assertEqual(
        r"""
            + start
            +   [@1,0:5='/var/ '<SEARCH>,1:1]
            +   [@2,6:11='/var/ '<SEARCH>,1:7]
            +   [@3,12:36='a kljafçl sadjfoiajuf / /'<WORDS>,1:13]
        """,
        tree.pretty(debug=1) )

    def test_onlyWord(self):
        expression = "var/ /var/"
        tree = HighlightWords._parser.parse( expression )

        self.assertEqual(
        r"""
            + start  [@1,0:9='var/ /var/'<WORDS>,1:1]
        """,
        tree.pretty(debug=1) )
