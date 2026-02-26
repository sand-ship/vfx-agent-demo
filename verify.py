import re
import sys

USDA_PATH = "vfx_project_alpha/shots/shot_010/scene_v01.usda"

def verify():
    with open(USDA_PATH) as f:
        content = f.read()

    errors = []

    # Check texture reference is v01
    if "iron_diffuse_v01.png" not in content:
        errors.append("Texture reference is not iron_diffuse_v01.png")

    # Check visibility is inherited
    vis_match = re.search(r'token visibility\s*=\s*"(\w+)"', content)
    if not vis_match or vis_match.group(1) != "inherited":
        errors.append(f"Visibility is '{vis_match.group(1) if vis_match else 'missing'}', expected 'inherited'")

    # Check focalLength is 45
    fl_match = re.search(r'float focalLength\s*=\s*([\d.]+)', content)
    if not fl_match or float(fl_match.group(1)) != 45:
        errors.append(f"focalLength is {fl_match.group(1) if fl_match else 'missing'}, expected 45")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)
    else:
        print("SUCCESS: All checks passed — texture is v01, visibility is inherited, focalLength is 45.")

if __name__ == "__main__":
    verify()
