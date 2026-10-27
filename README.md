# QuickSwap

A lightweight, customizable spear-swapping macro for Minecraft Java Edition, built with Python.

QuickSwap switches to your configured spear slot, performs a left click, and switches back to your selected return slot. The macro repeats while you hold the activation key, as long as it is enabled.

## Features

- Customizable activation key
- Configurable spear and return hotbar slots
- Adjustable interval between swap cycles
- Global **F1** enable/disable shortcut
- Always-on-top option with an animated toggle
- Automatically saved settings
- Compact dark-themed interface

## Download

1. Open the [Releases](../../releases) page.
2. Download `QuickSwap.exe` from the latest release.
3. Run it on Windows.

The executable does not require a separate Python installation.

## Usage

1. Launch QuickSwap.
2. Set your activation key, spear slot, return slot, and interval.
3. Press **F1** to enable the macro.
4. With Minecraft focused, hold the activation key to repeat the swap sequence.
5. Release the activation key to stop swapping, or press **F1** to disable the macro.

| Setting | Default |
| --- | --- |
| Activation key | V |
| Spear slot | 4 |
| Return slot | 1 |
| Interval | 295 ms |
| Always on top | Off |
| Enable/disable | F1 |

The interval is the delay between complete swap cycles, not the duration of each key press. Shorter intervals may result in input loss, it is recommended to stick to the default.

## Run from source

Requires Python 3 and the dependency below:

```bash
pip install customtkinter pynput
python main.py
```

## Build an executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name QuickSwap --collect-all customtkinter main.py
```

The built executable is saved to `dist\QuickSwap.exe`.

## Settings

QuickSwap saves preferences to:

```text
%APPDATA%\QuickSwap\settings.json
```

## Disclaimer

QuickSwap is an unofficial community utility and is not affiliated with or endorsed by Mojang Studios or Microsoft. Macros may be prohibited on some multiplayer servers. Check the rules before using it.

## License

Licensed under the [MIT License](LICENSE).