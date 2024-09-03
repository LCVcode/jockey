from pathlib import Path
import shutil


def post_build(interface) -> None:
    """Pyinstaller post build hook. Relocate binary to root of dist directory."""

    interface.write_line("  - <b>Relocating binaries</b>")
    for script in interface.pyproject_data["tool"]["poetry-pyinstaller-plugin"]["scripts"]:
        source = Path("dist", "pyinstaller", interface.platform, script)
        destination = Path("dist", f"{script}")

        if destination.exists():
            shutil.rmtree(destination)  # remove existing

        shutil.move(f"{source}", f"{destination}")
        interface.write_line(
            f"    - Updated " f"<success>{source}</success> -> " f"<success>{destination}</success>",
        )

    interface.write_line("  - <b>Cleaning</b>")
    shutil.rmtree(Path("build"))
    interface.write_line("    - Removed build directory")
