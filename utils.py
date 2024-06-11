import pathlib

def ensure_path_exists(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
