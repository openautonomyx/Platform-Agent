# Platform Agent - macOS App Packaging

## Requirements

- Xcode Command Line Tools
- create-dmg (Python)

```bash
pip install create-dmg
```

## Build macOS App

```bash
# Build the Python app
pyinstaller --name "Platform Agent" \
  --onefile \
  --windowed \
  --add-binary "src:platform_agent" \
  --hidden-import=aiohttp \
  --hidden-import=surrealdb \
  --hidden-import=pydantic \
  platform_agent/__init__.py

# Create DMG
create-dmg "dist/Platform Agent.app" \
  --volname "Platform Agent" \
  --window-pos 200 200 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "Platform Agent.app" /
  --icon-nonempty "Platform Agent.app" /
  --hide-extension "Platform Agent.app" \
  --app-drop-link 425 178 \
  "Platform-Agent.dmg"
```

## Code Signing

```bash
# Sign the app
codesign --sign "Developer ID Application: Your Name" \
  --deep \
  "dist/Platform Agent.app"

# Notarize
xcrun altool --notarize-app \
  -f "Platform-Agent.dmg" \
  -u "your@email.com" \
  -p "app-specific-password"
```

## DMG Structure

```
Platform-Agent.dmg/
├── Applications/
│   └── Platform Agent.app
├── & (symbolic link to /Applications)
└── .Drop Platform Agent Here.app to Install
```

## Package Options

- **DMG**: Simple disk image
- **PKG**: Installer with pre/post scripts
- **ZIP**: No signing required
- **APP**: Direct .app bundle