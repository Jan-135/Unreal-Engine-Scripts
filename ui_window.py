import unreal
import load_anim  # Hauptskript importieren

def show_import_dialog():
    """
    Zeigt einen Dialog an, ob das Skript ausgeführt werden soll.
    """
    title = "FBX Import Tool"
    message = "Möchtest du das Skript ausführen?"
    dialog_buttons = unreal.AppMsgType.YES_NO
    default_button = unreal.AppReturnType.NO

    user_choice = unreal.EditorDialog.show_message(
        title=title,
        message=message,
        message_type=dialog_buttons,
        default_value=default_button
    )

    if user_choice == unreal.AppReturnType.YES:
        unreal.log("Skript wird ausgeführt...")
        load_anim.create_unreal_folders(
            source_path="N:/GOLEMS_FATE/animations",
            unreal_base_path="/Game/ASSETS/Animations"
        )
        unreal.log("Skript erfolgreich abgeschlossen!")
    else:
        unreal.log("Skript wurde abgebrochen.")

# Dialog starten
show_import_dialog()
