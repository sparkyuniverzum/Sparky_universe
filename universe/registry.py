from pathlib import Path
import yaml

MODULES_PATH = Path(__file__).parent.parent / "modules"


def load_modules():
    modules = {}
    for module_dir in MODULES_PATH.iterdir():
        manifest = module_dir / "module.yaml"
        if manifest.exists():
            with open(manifest, "r") as f:
                data = yaml.safe_load(f)
                modules[data["name"]] = {**data, "path": module_dir}
    return modules
