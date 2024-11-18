import unreal
import os
import re

def extract_version(filename):
    """
    Extrahiert die Versionsnummer im Format 'v<number>' aus dem Dateinamen.
    """
    match = re.search(r"v(\d+)(?=\.\w+$)", filename)
    return int(match.group(1)) if match else -1

def find_latest_version(files):
    """
    Findet die Datei mit der höchsten Versionsnummer in einer Liste von Dateien.
    """
    latest_file = None
    highest_version = -1
    for file in files:
        version = extract_version(file)
        if version > highest_version:
            highest_version = version
            latest_file = file
    return latest_file

def create_unreal_folders(source_path, unreal_base_path):
    """
    Erstellt die gleiche Ordnerstruktur in Unreal wie auf der Festplatte
    und importiert nur die neueste Version, falls sie nicht bereits importiert wurde.
    """
    for character_folder in os.listdir(source_path):
        character_path = os.path.join(source_path, character_folder)
        if os.path.isdir(character_path):
            character_unreal_path = f"{unreal_base_path}/{character_folder}"
            create_folder_if_not_exists(character_unreal_path)
            
            for scene_folder in os.listdir(character_path):
                scene_path = os.path.join(character_path, scene_folder)
                if os.path.isdir(scene_path):
                    scene_unreal_path = f"{character_unreal_path}/{scene_folder}"
                    create_folder_if_not_exists(scene_unreal_path)

                    # Finde die neueste Version und importiere sie
                    animation_files = [f for f in os.listdir(scene_path) if f.endswith(".fbx")]
                    latest_file = find_latest_version(animation_files)
                    if latest_file:
                        animation_path = os.path.join(scene_path, latest_file)
                        unreal_asset_path = f"{scene_unreal_path}/{latest_file[:-4]}"
                        if not unreal.EditorAssetLibrary.does_asset_exist(unreal_asset_path):
                            import_fbx_to_unreal(scene_unreal_path, latest_file, animation_path)
                        else:
                            print(f"Neueste Version bereits importiert: {latest_file}")

def create_folder_if_not_exists(folder_path):
    """
    Erstellt den Ordner in Unreal, falls er noch nicht existiert.
    """
    if not unreal.EditorAssetLibrary.does_directory_exist(folder_path):
        unreal.EditorAssetLibrary.make_directory(folder_path)
        print(f"Ordner erstellt: {folder_path}")
    else:
        print(f"Ordner existiert bereits: {folder_path}")

def import_fbx_to_unreal(unreal_asset_path, animation_file, fbx_file_path):
    """
    Importiert die angegebene FBX-Datei nach Unreal und entfernt die Versionierung aus dem Asset-Namen.
    """
    # Entferne die Versionierung (z. B. 'v1', 'v2') aus dem Dateinamen
    base_name = re.sub(r"_v\d+$", "", animation_file[:-4])  # Entfernt '_v<number>' am Ende

    task = unreal.AssetImportTask()
    task.filename = fbx_file_path  # Pfad zur Datei auf der Festplatte
    task.destination_path = unreal_asset_path  # Zielordner in Unreal
    task.destination_name = f"anim_{base_name}"  # Name des Assets ohne Versionierung
    task.replace_existing = True  # Überschreibt bestehende Assets mit gleichem Namen, falls nötig

    # Definiere Import-Optionen mit FbxImportUI
    import_ui = unreal.FbxImportUI()
    import_ui.set_editor_property("import_as_skeletal", False)
    import_ui.set_editor_property("import_materials", True)
    import_ui.set_editor_property("import_textures", True)
    import_ui.set_editor_property("import_mesh", True)

    task.options = import_ui

    # Importiere die Datei
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    print(f"Import abgeschlossen: {fbx_file_path} als {task.destination_name} in {unreal_asset_path}")



# Beispiel: Quelle ist der lokale Ordner und Ziel ist der Unreal-Ordner
source_path = "N:/GOLEMS_FATE/animations"
unreal_base_path = "/Game/ASSETS/Animations"

# Struktur erstellen und importieren
create_unreal_folders(source_path, unreal_base_path)
print("Erfolgreich abgeschlossen!")
