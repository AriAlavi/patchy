from typing import Dict, List
from rimlink.rimlink import generateStructure, compareStructures, HashStructure
from tempfile import TemporaryDirectory
import pickle
import shutil
from pathlib import Path
import os
import zipfile
import time
import argparse

INSTRUCTION_FILENAME = "todo.patch"
BINARY_FILENAME_CREATE = "make_patch.exe"
BINARY_FILENAME_INSTALL = "install_patch.exe"

def get_file_depth(hash_structure: HashStructure) -> int:
    depth = 0
    while hash_structure.parent:
        hash_structure = hash_structure.parent
        depth += 1

    return depth


def get_folders_by_depth(structureList: List[HashStructure]) -> Dict[int, HashStructure]:
    assert isinstance(structureList, list), type(structureList)
    extra_folders = {}
    added_folders = set()

    for to_add in structureList:
        assert isinstance(to_add, HashStructure)
        if to_add in added_folders:
            continue

        if not to_add.file:
            depth = get_file_depth(to_add)
            if depth in extra_folders:
                extra_folders[depth].append(to_add)
            else:
                extra_folders[depth] = [to_add,]
            added_folders.union(added_folders)
        else:
            parent = to_add.parent
            if parent in added_folders:
                continue
            while parent:
                assert isinstance(parent, HashStructure)
                if not parent.file:
                    depth = get_file_depth(parent)
                    if depth in extra_folders:
                        extra_folders[depth].append(parent)
                    else:
                        extra_folders[depth] = [parent,]
                    added_folders.add(parent)

                parent = parent.parent

    return extra_folders

def create_zip(name, zip_name):

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for folder_name, subfolders, filenames in os.walk(name):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zip_ref.write(file_path, arcname=os.path.relpath(file_path, name))

    zip_ref.close()

def create_patch(baseFolder:str, newFolder:str) -> str:
    PATCH_FILENAME = "patch.zip"
    print("Starting patch creation")
    print("Finding diffs")
    diff = compareStructures(generateStructure(newFolder), generateStructure(baseFolder))
    if not diff:
        print("the files are the same")
        return

    add_count = len(diff["add"])
    remove_count = len(diff["delete"])
    modify_count = len(diff["modify"])
    print(f"There were {add_count} adds found")
    print(f"There were {remove_count} deletes found")
    print(f"There were {modify_count} modifies found")

    with TemporaryDirectory() as temp_dir:
        temp_folder_path = Path(temp_dir)
        instruction_filename_path = Path(temp_folder_path, INSTRUCTION_FILENAME)
        print("Saving install instructions")
        with open(instruction_filename_path, "wb") as file:
            pickle.dump(diff, file)
        
        print("Install instructions saved")

        for instruction_type in ["add", "modify", "delete"]:
            
            try:
                diff[instruction_type].remove(PATCH_FILENAME)
            except ValueError:
                pass
            try:
                diff[instruction_type].remove(BINARY_FILENAME_CREATE)
            except ValueError:
                pass
            try:
                diff[instruction_type].remove(BINARY_FILENAME_INSTALL)
            except ValueError:
                pass
            try:
                diff[instruction_type].remove(INSTRUCTION_FILENAME)
            except ValueError:
                pass
            

        print("Making copy folder structure")
        # add extra folders
        extra_folders = get_folders_by_depth(diff["add"] + diff["modify"])
        depths = list(extra_folders.keys())

        print("Depths", depths)
        for depth in sorted(depths):
            to_create_folders = extra_folders[depth]

            for to_create_folder in to_create_folders:
                assert isinstance(to_create_folder, HashStructure)
                new_folder = Path(temp_folder_path, to_create_folder.relativePath())
                print(f"Creating folder {new_folder}")
                try:
                    os.mkdir(new_folder)
                except FileExistsError:
                    pass

    
        print("Making copy file structure")
        
        # copy over the files that are to be modified or copied
        for to_copy in diff["add"] + diff["modify"]:
            assert isinstance(to_copy, HashStructure)
            if not to_copy.file:
                continue
            copy_from = to_copy.path()
            copy_to = Path(temp_folder_path, to_copy.relativePath()).absolute()
            print(f"Copy from {copy_from} to {copy_to}")
            shutil.copy(copy_from, copy_to)

        print("Copy file and folder structure made")
        print("Zipping patch")
        create_zip(temp_folder_path, PATCH_FILENAME)
        print("Patch zipped")
    
    return PATCH_FILENAME

        


def main():
    parser = argparse.ArgumentParser(prog = "Patchy")
    parser.add_argument("old_version")
    parser.add_argument("new_version")
    args =  parser.parse_args()
    
    create_patch(args.old_version, args.new_version)
    print("Execution complete")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()