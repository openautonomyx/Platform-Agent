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
# Generate certificate
security create-identity \
  -v "Developer ID Application: Your Name" \
  -d "Mac Developer" \
  -a "YOUR_APPLE_ID"

# Sign the app
codesign --sign "Developer ID Application: Your Name" \
  --deep \
  --force \
  "dist/Platform Agent.app"

# Verify
codesign -dv "dist/Platform Agent.app"
```

## Notarization (Required for distribution outside App Store)

### 1. App-Specific Password

```
1. Go to appleid.apple.com
2. Sign in → Security → App-Specific Passwords
3. Generate new password
```

### 2. Submit for Notarization

```bash
# Submit
xcrun altool --notarize-app \
  -f "Platform-Agent.dmg" \
  -u "your@email.com" \
  -p "app-specific-password" \
  --劈 @charset utf-8

# Check status (UUID from output)
xcrun altool --notarize-status \
  -u "your@email.com" \
  -p "app-specific-password" \
  --request-id "UUID-HERE"
```

### 3. Staple (Attach notarization to app)

```bash
xcrun stapler staple "dist/Platform Agent.app"
```

### 4. Verify

```bash
xcrun stapler validate "dist/Platform Agent.app"
# Should show: "validated"
```

## Notarization Tips

| Issue | Fix |
|-------|-----|
| "App is integrity protected" | `xattr -cr App.app` before signing |
| "Hardened Runtime" | Enable in Xcode → Capabilities |
| "Entitlements missing" | Include in Info.plist |
| Upload timeout | Use Transporter app instead |

## Entitlements

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

## ZIP Alternative (No notarization needed)

```bash
# For direct distribution
zip -r Platform-Agent.zip "Platform Agent.app"
# Users can extract and run locally
```

## Package Options

- **DMG**: Signed + Notarized (App Store, public distribution)
- **PKG**: Installer with scripts
- **ZIP**: No signing, simple distribution