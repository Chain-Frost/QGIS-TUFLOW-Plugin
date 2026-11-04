"""Build an installable ARR2019 test ZIP from the complete official plugin.

Run: python scripts/build_arr2019_test_plugin.py
Requires only Python's standard library; QGIS and Git are not required.
The official archive supplies dependencies absent from a normal source checkout.
"""

from configparser import ConfigParser
from copy import copy
from hashlib import sha256
from pathlib import Path, PurePosixPath
from shutil import copyfileobj
from urllib.error import URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026.1.7"
BASE_ARCHIVE = ROOT / "build" / f"tuflow-{VERSION}-official.zip"
OUTPUT_ARCHIVE = ROOT / "dist" / f"tuflow-{VERSION}-arr-dialog-test.zip"
DOWNLOAD_URL = f"https://plugins.qgis.org/plugins/tuflow/version/{VERSION}/download/"
BASE_COMMIT = "31ac8acf1bdee214c7278a185c4596842c5d0220"
# SHA-256 of upstream source bytes after CRLF-to-LF normalization.
BASE_HASHES = {
    "tuflow/tuflowqgis_dialog.py":
        "7168159d985da1cdbd96471c12e9b1c56f144effa94672880105c0898b896437",
    "tuflow/forms/ui_tuflowqgis_arr2016.py":
        "4a9e739f16d83febefb64805059e6bc1b2e2f1216543eb3c7f7c2541c9476426",
    "tuflow/forms/ui_tuflowqgis_arr2016.ui":
        "69ce365c7f6398e53087bfa00985fc511ddc4d38ff5e016826e34befbe26dadb",
}
REQUIRED_FILES = ("tuflow/__init__.py", "tuflow/metadata.txt",
                  "tuflow/pt/pytuflow/__init__.py")
DEPENDENCY_PREFIXES = (
    "tuflow/pt/", "tuflow/swangis/",
    "tuflow/convert_tuflow_model_gis_format/", "tuflow/runner/tuflow-runner/",
)


def validate_archive(archive: ZipFile, check_base: bool = True) -> None:
    """Reject incomplete, incompatible, ambiguous, or corrupt plugin packages."""
    infos = archive.infolist()
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        raise ValueError("The archive contains duplicate member names.")
    for name in names:
        path = PurePosixPath(name)
        if not path.parts or path.parts[0] != "tuflow" or ".." in path.parts or "\\" in name:
            raise ValueError(f"Unexpected ZIP member {name!r}; expected one tuflow/ root.")
    for name in REQUIRED_FILES:
        if name not in names or archive.getinfo(name).file_size == 0:
            raise ValueError(f"Incomplete official plugin: missing or empty {name}.")
    for prefix in DEPENDENCY_PREFIXES:
        if not any(info.filename.startswith(prefix) and info.filename.endswith(".py")
                   and info.file_size for info in infos):
            raise ValueError(f"Incomplete official plugin: missing Python dependency {prefix}.")
    metadata = ConfigParser(interpolation=None)
    metadata.read_string(archive.read("tuflow/metadata.txt").decode("utf-8-sig"))
    if metadata.get("general", "version", fallback="") != VERSION:
        raise ValueError(f"Expected official plugin version {VERSION}.")
    if check_base:
        for name, expected in BASE_HASHES.items():
            if name not in names:
                raise ValueError(f"Official package lacks {name}; cannot verify compatibility.")
            actual = sha256(archive.read(name).replace(b"\r\n", b"\n")).hexdigest()
            if actual != expected:
                raise ValueError(f"Official {name} differs from upstream {BASE_COMMIT}; "
                                 "refusing to overlay incompatible source.")
    bad_member = archive.testzip()
    if bad_member:
        raise ValueError(f"Archive CRC check failed for {bad_member}.")


def ensure_base_archive() -> None:
    if BASE_ARCHIVE.exists():
        return
    BASE_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    download_path = BASE_ARCHIVE.with_suffix(".download")
    try:
        print(f"Downloading official TUFLOW {VERSION}...")
        request = Request(DOWNLOAD_URL, headers={"User-Agent": "TUFLOW-ARR2019-test-builder"})
        with urlopen(request, timeout=60) as response, download_path.open("wb") as destination:
            copyfileobj(response, destination)
        with ZipFile(download_path) as archive:
            validate_archive(archive)
        download_path.replace(BASE_ARCHIVE)
    except (OSError, URLError, BadZipFile) as exc:
        raise RuntimeError(f"Could not download the official plugin: {exc}. "
                           f"Download {DOWNLOAD_URL} in a browser, save it as "
                           f"{BASE_ARCHIVE}, and run this script again.") from exc
    finally:
        download_path.unlink(missing_ok=True)


def main() -> None:
    overlays = {name: (ROOT / name).read_bytes() for name in BASE_HASHES}
    ensure_base_archive()
    OUTPUT_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = OUTPUT_ARCHIVE.with_suffix(".tmp")
    try:
        with ZipFile(BASE_ARCHIVE) as original:
            validate_archive(original)
            with ZipFile(temporary_output, "w", compresslevel=9) as result:
                result.comment = original.comment
                for info in original.infolist():
                    data = overlays[info.filename] if info.filename in overlays else original.read(info)
                    result.writestr(copy(info), data)
        with ZipFile(temporary_output) as result:
            validate_archive(result, check_base=False)
        temporary_output.replace(OUTPUT_ARCHIVE)
    finally:
        temporary_output.unlink(missing_ok=True)
    print(f"Built: {OUTPUT_ARCHIVE}")
    print("Install with QGIS Plugins > Manage and Install Plugins > Install from ZIP.")
    print("This test build retains version 2026.1.7; ARR2019 buttons read Run and Close.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(f"Build failed: {error}") from error
