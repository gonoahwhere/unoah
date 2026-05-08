# UNOAH

A simple UNO remake built in Python3.

## Project Structure

This project is contained inside the `unoah/` folder and runs as a Python module.

### `noah_uno/`

- Main package for UNOAH
- Contains all the game logic, rules and core functionality
- Handles:
    - Card generation and deck management
    - Player turns and game flow
    - Game rules (UNO mechanics)
- Entry point: `__main__.py`

## Dependencies

> Make sure you have Python3 installed. This may require installation for your OS

This project requires the following external library:

- wxPython (GUI framework)

## Scripts

### Installing dependencies

```bash
python3 -m pip install wxpython
```

### Running the game

> Make sure you are inside the `unoah/` directory.

#### Windows
```bash
python3 -m noah_uno
```

#### macOS / Linux
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m noah_uno
```
