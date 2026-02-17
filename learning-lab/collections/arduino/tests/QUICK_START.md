# Quick Start Guide - Arduino Learning Lab Tests

## 30-Second Setup

```bash
cd /sessions/laughing-serene-hawking/mnt/outputs/learning-lab/collections/arduino/tests
bash run-tests.sh
```

Expected output: ✅ **All tests passed!**

## What Gets Tested (Summary)

### 🎮 Game Logic (26 tests)
- **Debug Code Game**: 3 unique bugs, correct XP math, valid scenarios
- **Circuit Quiz**: 5 random questions, correct answers included, XP calculation
- **Component Matching**: 8 cards, 4 pairs, logical emoji-label mappings

### 💰 XP System (6 tests)
- Quest completion: 100 XP
- Debug game: correct × 10 XP
- Quiz game: correct × 10 XP
- Matching game: 50 XP flat
- Total: completedCount × 100 + bonusXp
- Level: floor(xp / 100) + 1

### 💾 Save/Load (4 tests)
- LocalStorage key format: `sparkcity_` + name
- Saves: completed quests, bonus XP, last played timestamp
- Auto-saves when state changes

### ⚛️ React Code (10 tests)
- All hooks (useState, useEffect) called before conditionals
- All components defined (App, SetupScreen, QuestView, etc.)
- React root renders to #root

### 📊 Content (8 tests)
- 12 projects with correct fields
- 12+ debug scenarios with valid bug lines
- 15 quiz questions
- 10+ component pairs

## Test Results

```
54 total tests
✅ 54 passed
❌ 0 failed

✓ All tests passed!
```

## Files Included

| File | Purpose |
|------|---------|
| `test-app.js` | Main test suite with 54 tests |
| `run-tests.sh` | Test runner with status messages |
| `extract-js.sh` | Extracts JS from HTML |
| `README.md` | Detailed documentation |
| `IMPLEMENTATION_SUMMARY.md` | Technical details |
| `QUICK_START.md` | This file |

## Common Commands

### Run all tests
```bash
bash run-tests.sh
```

### Run tests and see full output
```bash
node test-app.js
```

### Run tests and show only failures
```bash
node test-app.js 2>&1 | grep "✗"
```

### Extract and view JavaScript
```bash
bash extract-js.sh ../index.html | head -50
```

## Troubleshooting

### "Node.js not found"
```bash
which node
# or install from https://nodejs.org
```

### "File not found"
Ensure you're in the `tests` directory:
```bash
cd /sessions/laughing-serene-hawking/mnt/outputs/learning-lab/collections/arduino/tests
```

### Test failures?
1. Check error message in output
2. Look at the specific test in `test-app.js`
3. Review the code section mentioned in error
4. Run specific test categories

## What's Being Validated

### Prevents These Bugs
✅ All 3 lines marked as buggy in debug game
✅ Missing semicolons not detected
✅ Wrong case (digitalwrite vs digitalWrite) not caught
✅ Incorrect XP calculations
✅ Hooks called in conditionals
✅ Wrong emoji for components
✅ Quiz answers missing correct option
✅ Save/load key inconsistencies
✅ Missing components or functions

## Examples of Test Names

```
✓ Bug scenario 1: bugLine index is within answers array
✓ Quiz game selection returns 5 unique questions
✓ Component match game generates exactly 8 cards (4 pairs doubled)
✓ Total XP formula: completedCount * 100 + bonusXp
✓ All useState calls appear before conditional returns
✓ LocalStorage key format uses sparkcity_ prefix
✓ App component is defined
```

## Next Steps

1. ✅ **Run tests**: `bash run-tests.sh`
2. ✅ **Check results**: Should see "All tests passed!"
3. ✅ **Read documentation**: See `README.md` for details
4. ✅ **Integrate into CI/CD**: Use in automation pipelines
5. ✅ **Run after changes**: Test before committing

## Test Statistics

- **JavaScript Extraction**: ✓ 3 tests pass
- **Debug Code Game**: ✓ 15 tests pass
- **Circuit Quiz**: ✓ 5 tests pass
- **Component Match**: ✓ 6 tests pass
- **XP Calculations**: ✓ 6 tests pass
- **React Hooks**: ✓ 2 tests pass
- **Game Functions**: ✓ 3 tests pass
- **LocalStorage**: ✓ 4 tests pass
- **Projects Data**: ✓ 2 tests pass
- **Components**: ✓ 8 tests pass

**Total: 54/54 ✅**

## Performance

- Execution time: < 2 seconds
- No external dependencies
- Uses Node.js built-in modules only

## Support

- Full documentation: `README.md`
- Technical details: `IMPLEMENTATION_SUMMARY.md`
- Test code comments: `test-app.js`

---

**Status**: ✅ Ready to use
**Last Updated**: February 17, 2025
**Test Version**: 1.0
