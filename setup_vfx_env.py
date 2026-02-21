import os

def create_mock_vfx_project():
    base_dir = "vfx_project_alpha"
    folders = ["assets/hero_bot", "shots/shot_010", "textures", "render_logs"]
    
    for folder in folders:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    # 1. Create a texture (but give it a 'corrupt' name/location bug)
    with open(os.path.join(base_dir, "textures/iron_diffuse_v01.png"), "w") as f:
        f.write("fake_png_data")

    # 2. Create a 'Broken' USD file
    usd_content = """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Scope "World"
{
    def Mesh "Hero_Bot"
    {
        asset texture_file = @../../textures/iron_diffuse_v02.png@ 
        token visibility = "hidden"
        float3[] extent = [(-1, -1, -1), (1, 1, 1)]
        color3f[] primvars:displayColor = [(0.1, 0.5, 0.8)]
    }

    def Camera "Main_Cam"
    {
        float focalLength = 0
        float focusDistance = 5.0
    }
}
"""
    with open(os.path.join(base_dir, "shots/shot_010/scene_v01.usda"), "w") as f:
        f.write(usd_content)

    print(f"✅ Mock VFX Project created at: {os.path.abspath(base_dir)}")

if __name__ == "__main__":
    create_mock_vfx_project()