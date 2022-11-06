from pathlib import Path
from make_patch import create_patch

def test_make_patch():
    test_origin_folder = Path("test_files, RimworldMissingInteriorExterior")
    test_new_folder = Path("test_files, RimworldBase")

    patch_filename = create_patch(test_origin_folder, test_new_folder)
