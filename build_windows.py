"""One-file Windows build. Run with the project's virtual-environment Python."""
from pathlib import Path
import os
import struct
import subprocess
import sys

from game import BIRD, PALETTE, VERSION

ROOT = Path(__file__).resolve().parent


def make_icon(path):
    """Write a multi-resolution 32-bit ICO using our own bird sprite."""
    images = []
    for size in (16, 32, 48, 64):
        pixels = bytearray()
        for y in reversed(range(size)):
            for x in range(size):
                nx, ny = (x + 0.5) * 64 / size, (y + 0.5) * 64 / size
                distance = (nx-32)**2 + (ny-32)**2
                color = "#70c5ce" if distance < 29**2 else "#3b8791"
                alpha = 255 if distance <= 31**2 else 0
                sx, sy = int((nx-6.5)/3), int((ny-14)/3)
                if nx >= 6.5 and ny >= 14 and 0 <= sx < 17 and 0 <= sy < 12:
                    color = PALETTE.get(BIRD[sy][sx], color)
                red, green, blue = bytes.fromhex(color[1:])
                pixels.extend((blue, green, red, alpha))
        mask = bytes(((size+31)//32)*4*size)
        header = struct.pack("<IIIHHIIIIII", 40, size, size*2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
        images.append((size, header+pixels+mask))
    offset = 6 + 16 * len(images)
    entries = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    for size, data in images:
        entries.extend(struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    path.write_bytes(entries + b"".join(data for _, data in images))


def main():
    if sys.platform != "win32":
        raise SystemExit("Gere o executável de Windows em um computador Windows.")
    os.chdir(ROOT)
    build = ROOT / "build"
    temporary = ROOT / ".build-temp"
    build.mkdir(exist_ok=True)
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(build / "cache")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=True)
    icon = build / "flappy.ico"
    make_icon(icon)
    version_file = build / "version_info.txt"
    version_file.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers=(0, 2, 0, 0), prodvers=(0, 2, 0, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Flappy Bird'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('ProductName', 'Flappy Bird'),
    StringStruct('ProductVersion', '{VERSION}'),
    StringStruct('OriginalFilename', 'FlappyBird.exe')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
''', encoding="utf-8")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
                    "--windowed", "--name", "FlappyBird", "--icon", str(icon),
                    "--version-file", str(version_file), "--noupx", "--specpath", str(build),
                    "--distpath", str(ROOT / "dist"), "--workpath", str(build / "pyinstaller"),
                    str(ROOT / "game.py")], check=True)
    print(f"Build concluída: {ROOT / 'dist' / 'FlappyBird.exe'}")


if __name__ == "__main__":
    main()
