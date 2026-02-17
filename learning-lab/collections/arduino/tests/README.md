# Arduino Learning Lab - Automated Test Suite

A comprehensive test suite for the Arduino Learning Lab React application that validates JavaScript syntax, game logic, XP calculations, React hook ordering, and content correctness.

## Overview

The test suite consists of **54 automated tests** organized into 10 categories, ensuring the app functions correctly across all critical components.

## Test Categories

### 1. JavaScript Syntax Validation (3 tests)
- Ensures JavaScript code extracts cleanly from HTML
- Validates React imports and PROJECTS array existence
- Confirms all dependencies are properly loaded

### 2. Debug Code Game (15 tests)
- Validates 12+ bug scenarios exist
- Verifies each bug's `bugLine` index is within the answers array
- Ensures debug game returns exactly 3 unique bugs
- Validates XP calculation: `correctCount * 10`

### 3. Circuit Quiz Game (5 tests)
- Confirms 15 quiz questions exist in the pool
- Validates 5 questions are selected per game
- Ensures correct answer is included in shuffled options
- Verifies XP calculation: `correctCount * 10`
- Validates answer tracking mechanism

### 4. Component Matching Game (6 tests)
- Confirms 10+ component pairs exist
- Validates no duplicate labels
- Ensures emoji-label pairs are logical
- Confirms exactly 8 cards (4 pairs doubled)
- Verifies flat 50 XP reward
- Validates card shuffling

### 5. XP Math Validation (6 tests)
- Quest completion: 100 XP
- Total XP: `completedCount * 100 + bonusXp`
- Level formula: `Math.floor(xp / 100) + 1`
- Debug game XP: `correctCount * 10`
- Quiz game XP: `correctCount * 10`
- Match game XP: flat 50

### 6. React Hooks Order (2 tests)
- All `useState` calls before conditional returns
- All `useEffect` calls before conditional returns
- Prevents "invalid hook order" errors at runtime

### 7. Game Generation Functions (3 tests)
- Validates all three game generators exist
- Confirms correct return types
- Ensures proper object structure

### 8. LocalStorage Persistence (4 tests)
- Validates key format: `sparkcity_` + lowercase name
- Confirms saved data includes `completed`, `bonusXp`, `lastPlayed`
- Verifies auto-save in useEffect

### 9. Projects Data (2 tests)
- Confirms exactly 12 projects exist
- Validates all required fields in project objects

### 10. UI Components (8 tests)
- All component functions are defined
- React root properly renders to `#root` element
- Validates: App, SetupScreen, QuestView, MiniGameView, DebugCodeGame, CircuitQuizGame, ComponentMatchGame

## Running Tests

### Quick Start
```bash
cd tests
bash run-tests.sh
```

### Direct Node.js
```bash
node test-app.js
```

## Test Output

The test runner displays:
- ✅ Green checkmark for passing tests
- ❌ Red X for failing tests with error messages
- Summary of passed/failed/total tests
- Exit code 0 on success, 1 on failure

Example output:
```
✓ JS code extracts from HTML without errors
✓ JS code contains React imports
✓ JS code contains PROJECTS array
...
Total tests:  54
Passed:       54
Failed:       0

✓ All tests passed!
```

## Test Files

- **test-app.js** - Main test suite with 54 automated tests
- **run-tests.sh** - Test runner script with status messages
- **extract-js.sh** - Helper script to extract JavaScript from HTML
- **README.md** - This file

## What Gets Tested

### Code Structure
- React hooks properly ordered (before conditionals)
- All game generation functions exist
- All UI components defined
- Proper React root setup

### Game Logic
- Debug code: 3 unique bugs selected, XP = `correct * 10`
- Quiz: 5 unique questions, correct answer in options, XP = `correct * 10`
- Match: 8 cards (4 pairs × 2), flat 50 XP

### Content Accuracy
- 12 projects with all required fields
- 12+ bug scenarios with valid bugLine indices
- 15 quiz questions
- 10+ component pairs with logical emoji-label pairings

### XP System
- Quest completion: 100 XP
- Bonus XP accumulation
- Level progression: `level = Math.floor(xp / 100) + 1`

### Persistence
- LocalStorage key format
- Auto-save in useEffect
- Data structure validation

## Future Tests

Potential additions:
- Arduino code syntax validation (detecting case-sensitivity bugs)
- Component rendering tests using React Testing Library
- Integration tests for game flow
- Performance tests for large dataset operations
- Accessibility tests

## Troubleshooting

### "Node.js is not installed"
Install Node.js v14+ from https://nodejs.org

### "Could not find <script> tag"
Ensure the test runs from the `tests` directory and the HTML file is at `../index.html`

### Test failures
1. Read the error message carefully
2. Check the specific function/value mentioned
3. The test name indicates which area failed
4. Review the corresponding code section in index.html

## Requirements

- Node.js v14 or higher
- Bash shell
- Read-only access to `/index.html`

## Test Statistics

| Category | Tests | Status |
|----------|-------|--------|
| JavaScript Syntax | 3 | ✅ Pass |
| Debug Game | 15 | ✅ Pass |
| Circuit Quiz | 5 | ✅ Pass |
| Component Match | 6 | ✅ Pass |
| XP Math | 6 | ✅ Pass |
| React Hooks | 2 | ✅ Pass |
| Game Generation | 3 | ✅ Pass |
| LocalStorage | 4 | ✅ Pass |
| Projects Data | 2 | ✅ Pass |
| UI Components | 8 | ✅ Pass |
| **TOTAL** | **54** | **✅ Pass** |

## Notes

- Tests use Node.js built-in `assert` module (no external dependencies)
- All tests are read-only; they don't modify the HTML or localStorage
- Tests validate both structure (existence) and logic (calculations)
- Test execution is typically under 2 seconds
- Tests validate against common bugs found during development:
  - All 3 lines have bugs in debug game (now validates exactly 1 per scenario)
  - Wrong emoji for components (validated)
  - Incorrect XP math (validated)
  - React hook ordering (validated)
  - Missing quiz answers (validated)
