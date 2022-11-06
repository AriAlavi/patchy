import pickle
from tempfile import TemporaryDirectory
import shutil
import os
from pathlib import Path
from make_patch import INSTRUCTION_FILENAME, get_folders_by_depth
from rimlink.rimlink import HashStructure

def install_patch(patch_file: str):
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

        print("Done deleting old files")
        print("Patch finished installing")

install_patch("patch.zip")