import json
import unreal
import os
from pathlib import Path
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askdirectory
from tkinter import simpledialog, Tk, Label, Button


def get_material_map(path):
    """Loads the material mapping from a JSON file."""
    return json.load(path.open())


def get_file_location(object, channel, object_to_material_map):
    """Retrieves the file path for a specific object and channel from the material map."""
    for obj, channel_map in object_to_material_map.items():
        if object == obj:
            for chan, file in channel_map.items():
                if channel == chan:
                    return file


def create_material(asset_name, package_path):
    """Creates a new material asset in the specified package path."""
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
        print("Error: Material creation failed.")
        return None


def import_texture(file_path, destination_path):
    """Imports a texture from the specified file path into the destination path."""
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
        print(f"Error: Texture '{file_path}' import failed.")
        return None


def add_one_texture_to_material(material, texture, channel):
    """Adds a single texture to the material at the specified channel."""
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
    """Remaps the channels in the material map based on a provided dictionary."""
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
    """Adds all textures from the material map to the material."""
    for channel, origin in material_map.items():
        if origin:
            destination = unreal.EditorAssetLibrary.get_path_name(material)
            texture = import_texture(origin, destination)
            if texture:
                add_one_texture_to_material(material, texture, channel)


def select_json_file():
    """Prompts the user to select a JSON file."""
    json_file_path = askopenfilename(
        initialdir="N:/GOLEMS_FATE/character",
        title="Select a JSON file",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if json_file_path:
        print("Selected JSON file:", json_file_path)
        return json_file_path
    else:
        print("No file selected.")
        return None


def get_user_input():
    """
    Prompts the user for necessary inputs including the JSON file, asset name,
    and package path for material creation.
    """
    # Try to retrieve the selected folder path
    selected_paths = unreal.EditorUtilityLibrary.get_selected_folder_paths()

    if not selected_paths:
        raise ValueError("No folder selected in the Content Browser.")
    else:
        # Use the selected folder path
        content_path = selected_paths[0]
        
        # Remove "/All" prefix if present
        if content_path.startswith("/All/"):
            content_path = content_path.replace("/All", "", 1)
        
        unreal.log(f"Using selected folder: {content_path}")

    # Select the JSON file (Tkinter)
    json_file_path = select_json_file()

    # Prompt for asset name (Unreal dialog)
    asset_name = simpledialog.askstring("Asset Name", "Enter the name of the material:")
    if not asset_name:
        raise ValueError("No asset name provided.")

    return Path(json_file_path), asset_name, content_path


def show_start_dialog():
    """
    Displays a dialog asking the user if they want to proceed.
    Returns True if the user agrees, False if they cancel.
    """
    # Initialize Tkinter window
    root = Tk()
    root.title("Choose a JSON File")
    root.geometry("300x100")
    user_choice = {"continue": False}

    def on_continue():
        user_choice["continue"] = True
        root.destroy()

    def on_cancel():
        user_choice["continue"] = False
        root.destroy()

    Label(root, text="Please select a JSON file").pack(pady=10)
    Button(root, text="Select File", command=on_continue).pack(side="left", padx=20)
    Button(root, text="Cancel", command=on_cancel).pack(side="right", padx=20)

    root.mainloop()
    return user_choice["continue"]


def start_script():
    """Main function that orchestrates the process of material creation and texture import."""
    try:
        if not show_start_dialog():
            unreal.log_warning("Script was canceled by the user.")
            return

        json_path, asset_name, package_path = get_user_input()

        unreal.log(f"JSON Path: {json_path}")
        unreal.log(f"Asset Name: {asset_name}")
        unreal.log(f"Package Path: {package_path}")

        # Mapping channels for materials
        channel_remap = {
            "baseColor": unreal.MaterialProperty.MP_BASE_COLOR,
            "opacity": unreal.MaterialProperty.MP_OPACITY,
            "normalCamera": unreal.MaterialProperty.MP_NORMAL,
            "metalness": unreal.MaterialProperty.MP_METALLIC,
            "specularRoughness": unreal.MaterialProperty.MP_ROUGHNESS
        }

        object_to_material_map = get_material_map(json_path)
        mapped_data = remap_channels(object_to_material_map, channel_remap)
        print("*** Here is the new map:", mapped_data, "***")

        for obj, material_map in mapped_data.items():
            material = create_material(asset_name, package_path)
            if material:
                print(f"Material {asset_name} created for {obj}.")
                add_all_textures_to_material(material, material_map)

    except ValueError as e:
        unreal.log_error(f"Script aborted: {e}")
    except Exception as e:
        unreal.log_error(f"Error in script: {e}")


# Run the script
start_script()
