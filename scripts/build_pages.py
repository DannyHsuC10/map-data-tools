from pathlib import Path
from shutil import copy2, copytree, ignore_patterns
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "_site"
    output.mkdir(parents=True, exist_ok=True)
    copytree(root / "web", output, dirs_exist_ok=True, ignore=ignore_patterns("__pycache__"))
    python_dir = output / "python"
    python_dir.mkdir(exist_ok=True)
    for module in ("DXF_to_lapdata", "cone_to_ini", "lapdata_to_xy", "track_characterization", "track_pipeline"):
        copy2(root / f"{module}.py", python_dir)
    samples = output / "samples"
    samples.mkdir(exist_ok=True)
    for path in ("fsae_A_2025.dxf", "output_ACC/FST/FST_cone.dxf"):
        copy2(root / path, samples)
    (output / ".nojekyll").touch()


if __name__ == "__main__":
    main()
