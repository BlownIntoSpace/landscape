#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2024 Bailey Allen, bailey [at] blowninto.space
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
"""
Subtile
"""

import os
import locale

import inkex
from inkex.command import inkscape
from inkex.localization import inkex_gettext as _


class Subtile(inkex.EffectExtension):
    """Exports an SVG file as a set of raster tiles of given size and zoom."""

    def add_arguments(self, pars):
        pars.add_argument("--directory", type=str, default="~/")
        pars.add_argument("--zoom", type=int, default=5)
        pars.add_argument("--filetype", type=str, default="webp")
        pars.add_argument("--tilesize", type=int, default=256)


    def effect(self):
        pass

        



if __name__ == "__main__":
    Subtile().run()
