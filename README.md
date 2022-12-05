# bboxer-app

Lightweight bouding boxer demo app consuming API service 🪑

# Prerequisities

Requires Poetry and Python >= 3.8.

Install dependencies with Poetry and activate the environment:

```sh
poetry install --no-root
poetry shell
```

# Usage

Run the Python application:

```sh
bboxer-app [--url URL]
           [--no-save NO_SAVE]
           [images ...]
```

Positional arguments:
- `images` - HTTP/HTTPS URLs or paths to images.

Options:
- `--url URL` - overwrite default endpoint (useful for local testing)
- `--no-save` - Do not save resulting images (prints response instead)
