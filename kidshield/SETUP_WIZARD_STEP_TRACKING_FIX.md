# Setup Wizard Step Tracking Fix

## Problem Fixed

**Issue**: The "Continue Setup" button in the App Management screen was taking users back to Step 1 of the setup wizard instead of advancing to Step 3 (Time Limits).

**Root Cause**: The setup wizard state wasn't being preserved when navigating to other screens. Each time users returned to the setup wizard, it would restart at step 0.

## Solution Implemented

### 1. Step Parameter Support
- Modified `Screen.SetupWizard` to accept a `step` parameter
- Updated `SetupWizardScreen` to accept an `initialStep` parameter
- Added navigation argument handling for the step parameter

### 2. Proper Navigation Flow
- **App Management → Setup Wizard**: Now navigates to step 2 (Time Limits step)
- **Time Limits → Setup Wizard**: Now navigates to step 3 (Completion step)
- Each screen maintains context of where it came from

### 3. Enhanced Screen Integration
- Added `fromSetup` parameter to both App Management and Time Limits screens
- Added "Continue Setup" buttons that appear only when accessed from setup wizard
- Updated headers to show setup context (e.g., "Setup: Choose Apps - Step 2 of 4")

### 4. Navigation Graph Updates
- Added argument handling for step tracking
- Proper navigation with `popUpTo` to prevent back stack issues
- Consistent parameter passing between screens

## New Flow

1. **Setup Wizard Step 1**: Welcome → "Let's Get Started"
2. **Setup Wizard Step 2**: App Selection → "Choose Apps Now" → App Management Screen
3. **App Management**: Select apps → "Continue Setup" → **Setup Wizard Step 3**
4. **Setup Wizard Step 3**: Time Limits → "Set Time Limits" → Time Limits Screen  
5. **Time Limits**: Set limits → "Continue Setup" → **Setup Wizard Step 4**
6. **Setup Wizard Step 4**: Completion → "Start Using KidShield"

## Technical Changes

### Screen.kt
```kotlin
data object SetupWizard : Screen("setup_wizard?step={step}") {
    fun createRoute(step: Int = 0) = "setup_wizard?step=$step"
}

data object AppManagement : Screen("app_management?fromSetup={fromSetup}") {
    fun createRoute(fromSetup: Boolean = false) = "app_management?fromSetup=$fromSetup"
}

data object TimeLimits : Screen("time_limits?fromSetup={fromSetup}") {
    fun createRoute(fromSetup: Boolean = false) = "time_limits?fromSetup=$fromSetup"
}
```

### Navigation Logic
- App Management "Continue Setup" → `SetupWizard.createRoute(step = 2)`
- Time Limits "Continue Setup" → `SetupWizard.createRoute(step = 3)`
- Proper back stack management with `popUpTo`

## Benefits

1. **Correct Flow**: Users now progress through setup steps in the right order
2. **Context Preservation**: Setup state is maintained across screen transitions
3. **Clear Progress**: Users always know which step they're on
4. **Consistent Experience**: Same pattern for both app selection and time limits
5. **No Confusion**: No more jumping back to step 1 unexpectedly

The setup wizard now provides a smooth, logical progression where each "Continue Setup" button advances to the next appropriate step.