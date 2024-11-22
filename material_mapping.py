from pathlib import Path
import json
import unreal

def get_material_map(path):
    return json.load(path.open())

def get_file_location(object, channel, object_to_material_map):
    for obj, channel_map in object_to_material_map.items():
        if object == obj:
            for chan, file in channel_map.items():
                if channel == chan:
                    return file

def create_material(asset_name, package_path):
    # Erstelle Material Factory
    material_factory = unreal.MaterialFactoryNew()

    # AssetTools instanziieren
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    # Neues Material-Asset erstellen
    new_material = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.Material,
        factory=material_factory
    )

    if new_material:
        # Asset speichern
        unreal.EditorAssetLibrary.save_loaded_asset(new_material)
        return new_material
    else:
        print("Fehler: Material konnte nicht erstellt werden.")
        return None

def import_texture(file_path, destination_path):
    # Erstelle eine Import-Task
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str (file_path))
    task.set_editor_property("destination_path", destination_path)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)

    # Import durchführen
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    # Überprüfen, ob der Import erfolgreich war
    imported_asset = task.get_editor_property("imported_object_paths")
    if imported_asset:
        imported_texture = unreal.EditorAssetLibrary.load_asset(imported_asset[0])
        return imported_texture
    else:
        print(f"Fehler: Textur '{file_path}' konnte nicht importiert werden.")
        return None

def add_one_texture_to_material(material, texture, channel):
    # Use MaterialEditingLibrary
    editor_subsystem = unreal.MaterialEditingLibrary

    # Create a Texture Sample Expression
    texture_sample = editor_subsystem.create_material_expression(
        material,
        unreal.MaterialExpressionTextureSample,
    )
    texture_sample.texture = texture  # Assign the texture to the expression

    # Connect the texture to the specified material channel
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
        if not (origin == None):
            destination = unreal.EditorAssetLibrary.get_path_name(material)
            texture = import_texture(origin, destination)
            if texture:
                add_one_texture_to_material(material, texture, channel)



#Path zum Json file:
path = Path(r"N:\GOLEMS_FATE\crew\Jan\Scripts\NachhilfeMitJochen\test.json")

channel_remap = {
    "baseColor": unreal.MaterialProperty.MP_BASE_COLOR,
    "opacity" : unreal.MaterialProperty.MP_OPACITY,
    "normalCamera": unreal.MaterialProperty.MP_NORMAL,
    "metalness": unreal.MaterialProperty.MP_METALLIC,
    "specularRoughness": unreal.MaterialProperty.MP_ROUGHNESS
}

package_path = "/Game/MyMaterials"
asset_name = "MyNewMaterial"
object_to_material_map = get_material_map(path)
map = remap_channels(object_to_material_map, channel_remap )
print("***Hier ist die neue Map:", map, "***")

for obj, material_map in map.items():
    material = create_material(asset_name, package_path)
    
    print(obj)
    print("schau mal: ", material_map)
    add_all_textures_to_material(material, material_map)