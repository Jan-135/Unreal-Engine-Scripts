from pathlib import Path
import json
import unreal
import tkinter as tk
from tkinter import filedialog, simpledialog


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


def get_user_input():
    root = tk.Tk()
    root.withdraw()

    # JSON-Dateipfad auswählen
    json_path = filedialog.askopenfilename(
        title="Wähle die JSON-Datei",
        filetypes=[("JSON Files", "*.json")]
    )
    if not json_path:
        raise ValueError("Keine JSON-Datei ausgewählt.")

    # Asset-Name eingeben
    asset_name = simpledialog.askstring("Asset Name", "Gib den Namen des Materials ein:")
    if not asset_name:
        raise ValueError("Kein Asset-Name eingegeben.")

    # Package-Path eingeben
    package_path = simpledialog.askstring(
        "Package Path", "Gib den Zielordner für das Material ein (z.B. /Game/MyMaterials):"
    )
    if not package_path:
        raise ValueError("Kein Package-Path eingegeben.")

    return Path(json_path), asset_name, package_path


def start_script():
    try:
        json_path, asset_name, package_path = get_user_input()

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


# Start des Scripts
start_script()
