"""Utils for testing contaix."""

from importlib.resources import files
from pathlib import Path
from contaix import __package__ as package_name


test_data_files = files(package_name) / "tests" / "data"
test_data_path = Path(test_data_files)
test_data_dir = str(test_data_path.resolve())
