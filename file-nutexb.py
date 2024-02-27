#!/usr/bin/env python3

"""
GIMP Plug-in for the nutexb file format
"""

import gi

gi.require_version("Gimp", "3.0") # Needed Before Importing Gimp
from gi.repository import Gimp
gi.require_version("Gegl", "0.4") # Needed Before Importing Gegl
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

from sys import argv
from pathlib import Path
from subprocess import run

def get_ultimate_tex_path() -> Path:
    return Path(__file__).parent / "dependencies" / "ultimate_tex_cli.exe"

def thumbnail_nutexb(procedure, file, thumb_size, args, data):
    # Convert to PNG
    nutexb_path: Path = Path(file.peek_path())
    temp_png_path: Path = nutexb_path.parent / (nutexb_path.stem + ".png")
    ultimate_tex_path = get_ultimate_tex_path() 
    run([ultimate_tex_path, str(nutexb_path),  str(temp_png_path)], capture_output=True, check=True)

    # Load PNG
    procedure = Gimp.get_pdb().lookup_procedure("file-png-load")
    config = procedure.create_config()
    config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
    config.set_property("file", Gio.File.new_for_path(str(temp_png_path)))
    result = procedure.run(config)
    success = result.index(0)
    image = result.index(1)

    # Delete Temp Png
    temp_png_path.unlink()

    return Gimp.ValueArray.new_from_values([
        GObject.Value(Gimp.PDBStatusType, success),
        GObject.Value(Gimp.Image, image),
    ])

def save_nutexb(procedure, run_mode, image, n_drawables, drawables, file, metadata, config, data):
    Gimp.progress_init("Exporting nutexb image")

    path: Path = Path(file.peek_path())
    temp_png_file: Path = path.parent / (path.stem + ".png")
    nutexb_path: Path = path.parent / (path.stem + ".nutexb")
    procedure = Gimp.get_pdb().lookup_procedure("file-png-save")
    config = procedure.create_config()
    config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
    config.set_property("image", image)
    config.set_property("num-drawables", n_drawables)
    config.set_property("drawables", Gimp.ObjectArray.new(Gimp.Drawable, drawables, False))
    config.set_property("file", Gio.File.new_for_path(str(temp_png_file)))
    #config.set_property("interlaced", FALSE)
    #config.set_property("compression", compression)
    #config.set_property("bkgd", bkgd)
    #config.set_property("offs", offs)
    #config.set_property("phys", phys)
    #config.set_property("time", time)
    config.set_property("save-transparent", True)
    #config.set_property("optimize-palette", optimize_palette)
    result = procedure.run(config)
    success = result.index(0)

    """
    # TODO: Colorspace settings in gimp 2.99 where
    match ...:
        case linear:
            format = "BC7Unorm"
        case sRGB:
            format = "BC7Srgb"
        case _:
            format = "BC7Unorm"
    """
    
    format = "BC7Srgb"
    ultimate_tex_path = get_ultimate_tex_path() 
    run([ultimate_tex_path, str(temp_png_file), str(nutexb_path), "--format", format], capture_output=True, check=True)
    temp_png_file.unlink()
    Gimp.progress_end()

    return Gimp.ValueArray.new_from_values([
        GObject.Value(Gimp.PDBStatusType, Gimp.PDBStatusType.SUCCESS)
    ])

def load_nutexb(procedure, run_mode, file, metadata, flags, config, data):
    Gimp.progress_init("Loading nutexb image")
    # Convert to PNG
    nutexb_path: Path = Path(file.peek_path())
    temp_png_path: Path = nutexb_path.parent / (nutexb_path.stem + ".png")
    ultimate_tex_path = get_ultimate_tex_path() 
    run([ultimate_tex_path, str(nutexb_path),  str(temp_png_path)], capture_output=True, check=True)

    # Load PNG
    procedure = Gimp.get_pdb().lookup_procedure("file-png-load")
    config = procedure.create_config()
    config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
    config.set_property("file", Gio.File.new_for_path(str(temp_png_path)))
    result = procedure.run(config)
    success = result.index(0)
    image = result.index(1)

    # Delete Temp Png
    temp_png_path.unlink()

    Gimp.progress_end()
    return Gimp.ValueArray.new_from_values([
        GObject.Value(Gimp.PDBStatusType, success),
        GObject.Value(Gimp.Image, image),
    ]), flags


class FileNutexb (Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, "gimp30-python", None

    def do_query_procedures(self):
        return [ "file-nutexb-load-thumb",
                 "file-nutexb-load",
                 "file-nutexb-save" ]

    def do_create_procedure(self, name):
        match name:
            case "file-nutexb-save":
                procedure = Gimp.SaveProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, False, save_nutexb, None)
                procedure.set_image_types("*")
                procedure.set_documentation ("Save a Namco Universal Texture Binary (.nutexb) file.", "Save a Namco Universal Texture Binary (.nutexb) file.", name)
                procedure.set_menu_label("nutexb")
                procedure.set_extensions("nutexb")
            case "file-nutexb-load":
                procedure = Gimp.LoadProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, load_nutexb, None)
                procedure.set_menu_label("Nutexb")
                procedure.set_documentation ("Load a Namco Universal Texture Binary (.nutexb) file.", "Load a Namco Universal Texture Binary (.nutexb) file.", name)
                procedure.set_mime_types("image/nutexb")
                procedure.set_extensions("nutexb")
                procedure.set_thumbnail_loader("file-nutexb-load-thumb")
            case "file-nutexb-load-thumb":
                procedure = Gimp.ThumbnailProcedure.new (self, name, Gimp.PDBProcType.PLUGIN, thumbnail_nutexb, None)
                procedure.set_documentation ("Loads a thumbnail from a nutexb file.", "Loads a thumbnail from a nutexb file.", name)
        procedure.set_attribution("Carlos Aguilar", "Carlos Aguilar", "2024") 
        
        return procedure

# Run

Gimp.main(FileNutexb.__gtype__, argv)
