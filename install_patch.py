import pickle
from tempfile import TemporaryDirectory
import shutil
import traceback
import os
from pathlib import Path
from make_patch import INSTRUCTION_FILENAME, get_folders_by_depth
from rimlink.rimlink import HashStructure
import time

def install_patch(patch_file: str):
    print("Starting Patch installation")
    assert ".zip" in patch_file
    with TemporaryDirectory() as temp_dir:
        temp_folder_path = Path(temp_dir)
        print("Unpacking patch")
        shutil.unpack_archive(patch_file, temp_folder_path)
        print("Patch unpacked")
        instruction_file_path = Path(temp_folder_path, INSTRUCTION_FILENAME)

        print("Copying over folders")
        with open(instruction_file_path, "rb") as instruction_file:
            instructions = pickle.load(instruction_file)
            assert isinstance(instructions, dict)
            assert [isinstance(x, list) for x in instructions.values()]
        
        add_folders = get_folders_by_depth(instructions["add"])

        for depth in sorted(add_folders.keys()):
            for add_folder in add_folders[depth]:
                assert isinstance(add_folder, HashStructure), type(add_folder)
                if add_folder.relativePath() == "":
                    continue
                try:
                    os.mkdir(add_folder.relativePath())
                except FileExistsError:
                    pass

        print("Folders copied over")
        print("Copying over files")
        for new_file in instructions["add"]:
            assert isinstance(new_file, HashStructure)
            if not new_file.file:
                continue
                
            new_file_current_path = Path(temp_folder_path, new_file.relativePath())
            shutil.copy(new_file_current_path, new_file.relativePath())

        print("Now doing files overwrites")

        for new_file in instructions["modify"]:
            assert isinstance(new_file, HashStructure)
            if not new_file.file:
                continue

            os.remove(new_file.relativePath())
                
            new_file_current_path = Path(temp_folder_path, new_file.relativePath())
            shutil.copy(new_file_current_path, new_file.relativePath())

        print("Done copying over all files")
        print("Now deleting old files")
        for delete_file in instructions["delete"]:
            assert isinstance(delete_file, HashStructure)
            if delete_file.file:
                try:
                    os.remove(delete_file.relativePath())
                except FileNotFoundError:
                    pass
        print("Now deleting old folders")
        for delete_file in instructions["delete"]:
            assert isinstance(delete_file, HashStructure)
            if not delete_file.file:
                try:
                    shutil.rmtree(delete_file.relativePath())
                except Exception:
                    pass

        print("Done deleting old files and folders")
        print("Patch finished installing")




if __name__ == "__main__":
    try:
        install_patch("patch.zip")
    except Exception as e:
        print(e)
        traceback.print_exc()
        print("Execution Failed!")
    print("Execution complete")
    while True:
        time.sleep(60)