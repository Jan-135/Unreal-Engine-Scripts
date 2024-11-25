import json
import unreal
import os

from pathlib import Path
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askdirectory
from tkinter import Tk
from tkinter import filedialog, simpledialog
from tkinter.filedialog import askopenfilename
from tkinter import Tk, Label, Button

def get_material_map(path):
    return json.load(path.open())


def get_file_location(object, channel, object_to_material_map):
    for obj, channel_map in object_to_material_map.items():
        if object == obj:
            for chan, file in channel_map.items():
                if channel == chan:
                    return file


def create_material(asset_name, package_path):
    material_factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    new_material = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.Material,
        factory=material_factory
    )

    if new_material:
        unreal.EditorAssetLibrary.save_loaded_asset(new_material)
        return new_material
    else:
        print("Fehler: Material konnte nicht erstellt werden.")
        return None


def import_texture(file_path, destination_path):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(file_path))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_asset = task.get_editor_property("imported_object_paths")
    if imported_asset:
        imported_texture = unreal.EditorAssetLibrary.load_asset(imported_asset[0])
        return imported_texture
    else:
        print(f"Fehler: Textur '{file_path}' konnte nicht importiert werden.")
        return None


def add_one_texture_to_material(material, texture, channel):
    editor_subsystem = unreal.MaterialEditingLibrary
    texture_sample = editor_subsystem.create_material_expression(
        material,
        unreal.MaterialExpressionTextureSample,
    )
    texture_sample.texture = texture

    if channel == unreal.MaterialProperty.MP_NORMAL:
        texture_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    editor_subsystem.connect_material_property(texture_sample, "RGB", channel)


def remap_channels(data, remap_dict):
    updated_data = {}
    for obj, channels in data.items():
        updated_channels = {}
        for old_channel, texture_path in channels.items():
            new_channel = remap_dict.get(old_channel)
            if new_channel:
                updated_channels[new_channel] = texture_path
        updated_data[obj] = updated_channels
    return updated_data


def add_all_textures_to_material(material, material_map):
    for channel, origin in material_map.items():
        if origin:
            destination = unreal.EditorAssetLibrary.get_path_name(material)
            texture = import_texture(origin, destination)
            if texture:
                add_one_texture_to_material(material, texture, channel)

def select_json_file():
    json_file_path = askopenfilename(
        initialdir="N:/GOLEMS_FATE/character",
        title="Wähle die JSON-Datei aus",
        filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")]
    )
    if json_file_path:
        print("Gewählte JSON-Datei:", json_file_path)
        return json_file_path
    else:
        print("Keine Datei ausgewählt.")
        return None

def get_user_input():
    # Versuche, den ausgewählten Ordner zu ermitteln
    selected_paths = unreal.EditorUtilityLibrary.get_selected_folder_paths()

    if not selected_paths:
        raise ValueError("Kein Ordner im Content Browser aktiv oder ausgewählt.")
    else:
        # Verwende den ausgewählten Ordnerpfad
        content_path = selected_paths[0]
        
        # Entferne das `/All`-Präfix, falls vorhanden
        if content_path.startswith("/All/"):
            content_path = content_path.replace("/All", "", 1)
        
        unreal.log(f"Verwende ausgewählten Ordner: {content_path}")


    # JSON-Dateipfad auswählen (Tkinter verwenden)
    json_file_path = select_json_file()

    # Asset-Name eingeben (Unreal-Dialog)
    asset_name = simpledialog.askstring("Asset Name", "Gib den Namen des Materials ein:")
    if not asset_name:
        raise ValueError("Kein Asset-Name eingegeben.")

    return Path(json_file_path), asset_name, content_path


# Beispiel-Aufruf: Dies ersetzt den vorherigen Aufruf von `get_user_input`.
def show_start_dialog():
    """
    Zeigt ein Dialogfenster an, um den Benutzer zu fragen, ob er fortfahren möchte.
    Gibt `True` zurück, wenn der Benutzer fortfahren möchte, und `False` bei Abbruch.
    """
    # Tkinter-Hauptfenster initialisieren
    root = Tk()
    root.title("Chose a Json-File")
    root.geometry("300x100")
    user_choice = {"continue": False}

    def on_continue():
        user_choice["continue"] = True
        root.destroy()

    def on_cancel():
        user_choice["continue"] = False
        root.destroy()

    Label(root, text="Please Select a Json-File?").pack(pady=10)
    Button(root, text="Select File", command=on_continue).pack(side="left", padx=20)
    Button(root, text="Cancel", command=on_cancel).pack(side="right", padx=20)

    root.mainloop()
    return user_choice["continue"]


# Beispiel-Aufruf
def start_script():
    try:
        if not show_start_dialog():
            unreal.log_warning("Script wurde vom Benutzer abgebrochen.")
            return

        json_path, asset_name, package_path = get_user_input()

        unreal.log(f"JSON-Pfad: {json_path}")
        unreal.log(f"Asset-Name: {asset_name}")
        unreal.log(f"Package-Pfad: {package_path}")

        # Füge hier deine weiteren Verarbeitungsschritte ein.

        channel_remap = {
            "baseColor": unreal.MaterialProperty.MP_BASE_COLOR,
            "opacity": unreal.MaterialProperty.MP_OPACITY,
            "normalCamera": unreal.MaterialProperty.MP_NORMAL,
            "metalness": unreal.MaterialProperty.MP_METALLIC,
            "specularRoughness": unreal.MaterialProperty.MP_ROUGHNESS
        }

        object_to_material_map = get_material_map(json_path)
        mapped_data = remap_channels(object_to_material_map, channel_remap)
        print("*** Hier ist die neue Map:", mapped_data, "***")

        for obj, material_map in mapped_data.items():
            material = create_material(asset_name, package_path)
            if material:
                print(f"Material {asset_name} für {obj} erstellt.")
                add_all_textures_to_material(material, material_map)

    except ValueError as e:
        unreal.log_error(f"Script abgebrochen: {e}")
    except Exception as e:
        unreal.log_error(f"Fehler im Script: {e}")


# Skript starten
start_script()
