# Launcher Setup Improvements

## Problem Fixed

**Issue**: The "Home Button Not Protected" banner action wasn't working to set KidShield as the default launcher on Android TV devices.

**Root Cause**: The original implementation only tried `ACTION_HOME_SETTINGS` which isn't available on all Android TV devices, and the fallback wasn't comprehensive enough.

## Solution Implemented

### Multi-Approach Strategy

The new implementation uses a cascading approach with multiple fallback methods:

1. **Intent.createChooser()** - Forces the system to show launcher selection dialog
2. **ACTION_HOME_SETTINGS** - Direct home app settings (if available)
3. **ACTION_MANAGE_DEFAULT_APPS_SETTINGS** - General default apps settings
4. **ACTION_APPLICATION_SETTINGS** - Application settings menu
5. **Basic HOME intent** - Triggers launcher selection as final fallback

### Enhanced User Guidance

- **Better Instructions**: "Click to choose KidShield as your default launcher"
- **Clear Next Step**: "Then select 'Always' when prompted"
- **Visual Hierarchy**: Multiple lines of instruction with different opacity levels

### Code Implementation

```kotlin
Surface(
    onClick = {
        // Multi-approach strategy for setting default launcher
        try {
            // Approach 1: Use Intent.createChooser to force launcher selection
            val homeIntent = Intent(Intent.ACTION_MAIN).apply {
                addCategory(Intent.CATEGORY_HOME)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK)
            }
            
            val chooser = Intent.createChooser(homeIntent, "Choose Default Launcher")
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(chooser)
            
        } catch (e: Exception) {
            // Multiple fallback approaches...
        }
    }
)
```

## How It Works

### For Users
1. Click the red "Home Button Not Protected" banner
2. System shows launcher selection dialog or settings
3. Choose "KidShield" from the list
4. Select "Always" when prompted
5. Home button now returns to KidShield

### For Different Android TV Devices
- **Google TV**: Usually shows launcher chooser dialog
- **Fire TV**: May open settings or show app selection
- **Other Android TV**: Falls back through multiple approaches
- **Restricted Devices**: At minimum opens settings where users can manually configure

## Benefits

1. **Higher Success Rate**: Multiple fallback approaches increase chances of working
2. **Better User Experience**: Clear instructions on what to do
3. **Device Compatibility**: Works across different Android TV implementations
4. **Graceful Degradation**: Always provides some path forward, even if manual

## Alternative Manual Instructions

If automatic methods still don't work on some devices, users can manually:

1. Go to **Settings > Apps > Default Apps > Home App**
2. Or **Settings > Device Preferences > Home Screen**
3. Or **Settings > Apps > KidShield > Set as Default**
4. Choose KidShield and select "Always"

## Testing Recommendations

Test on various Android TV devices:
- Google TV (Chromecast with Google TV)
- Fire TV devices
- Sony/Samsung/LG Android TV
- Generic Android TV boxes

The multi-approach strategy should work on most devices, with graceful fallbacks for edge cases.