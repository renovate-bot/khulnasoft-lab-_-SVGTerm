# SVG Terminal Recorder

[![Tests](https://github.com/khulnasoft-lab/svgterm/actions/workflows/test.yml/badge.svg)](https://github.com/khulnasoft-lab/svgterm/actions/workflows/test.yml)
[![PyPI Version](https://img.shields.io/pypi/v/svgterm?color=%2334D058)](https://pypi.org/project/svgterm/)
[![Python Versions](https://img.shields.io/pypi/pyversions/svgterm.svg)](https://pypi.org/project/svgterm/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/pypi/l/svgterm.svg)](https://opensource.org/licenses/BSD-3-Clause)

A modern terminal recorder that renders your command line sessions as standalone SVG animations or still frames.

## ✨ Features

- 🎥 Record terminal sessions or render existing recordings
- 🖼️ Generate lightweight, embeddable SVG animations or still frames
- 🎨 Customize appearance with themes and templates
- 🚀 Fast rendering with modern Python (3.7+)
- 📦 Easy installation via pip
- 🧩 Extensible architecture with a clean API

## 📦 Installation

```bash
# Requires Python 3.7+
pip install svgterm
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/khulnasoft-lab/svgterm.git
cd svgterm

# Install in development mode with all dependencies
pip install -e '.[dev]'

# Run tests
pytest
```

### System Packages

| OS | Installation |
|----|-------------|
| **macOS** | `brew install svgterm` |
| **Arch Linux** | `pacman -S svgterm` |
| **NixOS** | `nix-env -iA nixos.svgterm` |
| **FreeBSD** | `pkg install py39-svgterm` |

## 🚀 Basic Usage

### Record and render a terminal session

```bash
# Record a terminal session and save as animation.svg
svgterm -o animation.svg

# Record a specific command
svgterm -c 'ls -la' -o listing.svg

# Generate still frames instead of animation
svgterm -s -o frame.svg
```

### Render an existing recording

```bash
# Render an asciicast recording
svgterm render recording.cast -o animation.svg
```

### Advanced Options

```bash
# Set terminal size (columns x rows)
svgterm -g 80x24 -o output.svg

# Set minimum/maximum frame duration (ms)
svgterm -m 50 -M 1000 -o output.svg

# Use a custom template
svgterm -t my_template -o output.svg
```

## 🎨 Customization

### Templates

Create custom SVG templates in `~/.config/svgterm/templates/`. See the [templates documentation](docs/templates.md) for details.

### Themes

Customize colors and styling with themes. Place theme files in `~/.config/svgterm/themes/`.

## 📚 Documentation

For more detailed documentation, see:

- [Command Line Reference](docs/cli.md)
- [API Documentation](docs/api.md)
- [Creating Templates](docs/templates.md)
- [Examples](docs/examples.md)

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.
Start recording with:

```
$ svgterm
Recording started, enter "exit" command or Control-D to end
```

You are now in a subshell where you can type your commands as usual.
Once you are done, exit the shell to end the recording:

```
$ exit
Recording ended, file is /tmp/svgterm_exp5nsr4.svg
```
Then, use your favorite web browser to play the animation:
```
$ firefox /tmp/svgterm_exp5nsr4.svg
```

Finally, embedding the animation in e.g. a [README.md](README.md) file on GitHub can
be achieved with a relative link to the animation:
```markdown
![Example](./docs/examples/awesome_window_frame.svg)
```

See the [manual page](man/svgterm.md) for more details.

## Dependencies
svgterm uses:
* [pyte](https://github.com/selectel/pyte) to render the terminal screen
* [lxml](https://github.com/lxml/lxml) to work with SVG data
