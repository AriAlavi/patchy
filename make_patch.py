from typing import Dict, List
from rimlink.rimlink import generateStructure, compareStructures, HashStructure
from tempfile import TemporaryDirectory
import pickle
import shutil
from pathlib import Path
import os
import zipfile


INSTRUCTION_FILENAME = "todo.patch"

def get_file_depth(hash_structure: HashStructure) -> int:
    depth = 0
    while hash_structure.parent:
        hash_structure = hash_structure.parent
        depth += 1

    return depth


def get_folders_by_depth(structureList: List[HashStructure]) -> Dict[int, HashStructure]:
    assert isinstance(structureList, list), type(structureList)
    extra_folders = {}
    for to_add in structureList:
        assert isinstance(to_add, HashStructure)
        if not to_add.file:
            depth = get_file_depth(to_add)
            if depth in extra_folders:
                extra_folders[depth].append(to_add)
            else:
                extra_folders[depth] = [to_add,]

    return extra_folders

def create_zip(name, zip_name):

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for folder_name, subfolders, filenames in os.walk(name):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zip_ref.write(file_path, arcname=os.path.relpath(file_path, name))

    zip_ref.close()

def create_patch(baseFolder:str, newFolder:str) -> str:
    diff = compareStructures(generateStructure(newFolder), generateStructure(baseFolder))
    if not diff:
        print("the files are the same")
        return

    with TemporaryDirectory() as temp_dir:
        temp_folder_path = Path(temp_dir)
        instruction_filename_path = Path(temp_folder_path, INSTRUCTION_FILENAME)

        with open(instruction_filename_path, "wb") as file:
            pickle.dump(diff, file)


        # add extra folders
        extra_folders = get_folders_by_depth(diff["add"])
        depths = list(extra_folders.keys())


        for depth in sorted(depths):
            to_create_folders = extra_folders[depth]

            for to_create_folder in to_create_folders:
                assert isinstance(to_create_folder, HashStructure)
                os.mkdir(Path(temp_folder_path, to_create_folder.relativePath()))
            

        # copy over the files that are to be modified or copied
        for to_copy in diff["add"] + diff["modify"]:
            assert isinstance(to_copy, HashStructure)
            if not to_copy.file:
                continue
            copy_from = to_copy.path()
            copy_to = Path(temp_folder_path, to_copy.relativePath()).absolute()
            print(f"Copy from {copy_from} to {copy_to}")
            shutil.copy(copy_from, copy_to)

        print(temp_folder_path)
        for x in os.listdir(temp_folder_path):
            print(x)

        create_zip(temp_folder_path, "patch.zip")

        


def main():
    patch_name = create_patch(".git", "rimlink")


if __name__ == "__main__":
    main()