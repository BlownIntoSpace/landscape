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
A script that slices an svg file into multiple tiles, of a given size and zoom level.

The intended usecase is exporting a large svg into tiles for use with programs like leaflet.js
where a large image is broken into a directory structure e.g. (z/x/y.*) indicating the
zoom level and x/y coordinates of the tile.

Similar functionality could be achieved with the 'Export Slices' extension,
but that requires manual placement of the slices, which can be tedious and prone to error for large images.
It could also be achived simply by exporting the image to a large png, then slicing it with 
a program like gdal2tiles, but that requires additional setup and is not always reliable, and also places
a limit on the maximum zoom level achivable as the image is rasterized before slicing, and inkscape can only 
export pngs up to around 32000x32000 pixels in size.

This script instead attepts to perform the slicing directly on the svg file, and export each
slice as an individual image.

"""

import os
import locale
import threading
import numpy as np
from pathlib import Path
from PIL import Image


import inkex
from inkex.command import inkscape
from inkex.localization import inkex_gettext as _

# Enable debugging for this extension
DEBUG = False

class Tile:
    def __init__(self, x:int, y:int, z:int, size:int,inkscape_area:str):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.inkscape_area = inkscape_area

    def __str__(self):
        return f"Tile(x:{self.x}, y:{self.y}, z:{self.z}, size:{self.size})"

    def __repr__(self):
        return f"Tile(x:{self.x}, y:{self.y}, z:{self.z}, size:{self.size})"


class Subtile(inkex.EffectExtension):
    """Exports an SVG file as a set of raster tiles of given size and zoom."""

    def __init__(self):
        super(Subtile,self).__init__()

    def add_arguments(self, pars):
        pars.add_argument("--directory", type=Path, default=Path("~"), help="Directory to save the tiles to")
        pars.add_argument("--split_layers",type=inkex.Boolean, default=False, help="Split the SVG into into separate tilesets for each layer.")
        pars.add_argument("--zoom", default=5,type=int, help="Maximum zoom level to export to.")
        pars.add_argument("--filetype", default="webp", help="Filetype to save the tiles as.")
        pars.add_argument("--tilesize", default=256, type=int,help="Size of the tiles in pixels.")
        pars.add_argument("--ignore_transparent", type=inkex.Boolean, default=True, help="Ignore transparent tiles.")
    

    def get_image_properties(self):
        svg = inkex.load_svg(self.options.input_file).getroot()

        self.width = svg.viewport_height
        self.height = svg.viewport_width

        # Attempt to center the image bounds
        self.x_origin = 0
        self.y_origin = 0

        self.size = max(self.width,self.height)

        if self.width > self.height:
            self.y_origin = (self.height - self.width) / 2
        elif self.height > self.width:
            self.x_origin = (self.width - self.height) / 2
        self.options.input_file
        
    def format_filename(self, x:int, y:int, z:int,filetype=None) -> Path:
        if filetype is None:
            filetype = self.options.filetype
        return self.options.directory.joinpath(f"{z}/{x}/{y}.{filetype}")

    def generate_tile_specs(self):
        tiles = []
        for z in range(0,self.options.zoom):
            n = self.size / 2**z
            x_index = 0
            for x in np.arange(self.x_origin,self.x_origin + self.size,n):
                y_index = 0
                for y in np.arange(self.y_origin,self.y_origin + self.size,n):
                    tiles.append(
                        Tile(x=x_index,
                            y=y_index,
                            z=z,
                            size=self.options.tilesize,
                            inkscape_area=f"{x}:{y}:{x+n}:{y+n}"
                            )
                        )
                    y_index += 1
                x_index += 1

        return tiles

    def export_tiles(self,tiles:list[Tile]):
        for tile in tiles:
            self.export_tile(tile)



    def export_tile(self, tile:Tile):
        filename = self.format_filename(tile.x,tile.y,tile.z)
        filename.parent.mkdir(parents=True,exist_ok=True)
        svg_file = self.options.input_file
        kwargs = {
            "export-overwrite": True,
            "export-filename": self.format_filename(tile.x,tile.y,tile.z,"png"),
            "export-area": tile.inkscape_area,
            "export-width": self.options.tilesize,
            "export-height": self.options.tilesize,
        }

        inkscape(svg_file,**kwargs)
        image = Image.open(kwargs["export-filename"])

        # Delete transparent images if the option is set
        if image.getextrema()[-1] == (0,0) and self.options.ignore_transparent:
            os.remove(kwargs["export-filename"])
            return
        elif self.options.filetype != "png": # Convert to the desired format
            image.save(filename.as_posix())
            os.remove(kwargs["export-filename"])
        debug(f"Tile saved as {filename}")

    def effect(self):
        # Create path if it doesnt exist        
        self.options.directory.mkdir(exist_ok=True)
        # if any(self.options.directory.iterdir()): # Warn the user if the directory is not empty
        #     inkex.utils.debug(f"Warning! Directory not empty, files may be overwritten.")
        
        # Initialise image properties
        self.get_image_properties()

        thread_count = 4

        tile_specs = self.generate_tile_specs()

        batch_tiles = [tile_specs[i::thread_count] for i in range(thread_count)]

        threads = []
    
        for tiles in batch_tiles:
            threads.append(threading.Thread(target=self.export_tiles, args=(tiles,)))
        
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        return self.options.input_file
        


def debug(msg):
    """Print a debug message if DEBUG is True."""
    if DEBUG:
        inkex.utils.debug(msg)

if __name__ == "__main__":
    Subtile().run()

