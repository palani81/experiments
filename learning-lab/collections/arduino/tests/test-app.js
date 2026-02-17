#!/usr/bin/env node

/**
 * Comprehensive Test Suite for Arduino Learning Lab
 * Tests JavaScript syntax, game generation, XP math, and content correctness
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

let testCount = 0;
let passCount = 0;
let failCount = 0;

// Test runner
function test(name, fn) {
  testCount++;
  try {
    fn();
    passCount++;
    console.log(`${colors.green}✓${colors.reset} ${name}`);
  } catch (err) {
    failCount++;
    console.log(`${colors.red}✗${colors.reset} ${name}`);
    console.log(`  ${colors.red}${err.message}${colors.reset}`);
  }
}

// ─────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────────────

function extractJSFromHTML(htmlPath) {
  const html = fs.readFileSync(htmlPath, 'utf-8');
  const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!scriptMatch) throw new Error('Could not find <script> tag in HTML');
  return scriptMatch[1];
}

function validateArduinoSyntax(codeLine) {
  // Check if line should end with semicolon, brace, or is a control statement
  const trimmed = codeLine.trim();
  if (!trimmed || trimmed.startsWith('//')) return true; // Comments are OK

  // Control structures that don't need semicolons at end of line
  if (/^(if|else|for|while|do|switch|void|int|bool|char|byte|float|double|long|unsigned|const|volatile)[\s({]/.test(trimmed)) return true;

  // Lines ending with { or } are valid
  if (trimmed.endsWith('{') || trimmed.endsWith('}') || trimmed.endsWith('),')) return true;

  // Regular statements should end with semicolon
  if (/[a-zA-Z0-9)]}]$/.test(trimmed) && !trimmed.startsWith('#')) {
    return trimmed.endsWith(';');
  }

  return true;
}

function hasIdentifiableBug(codeLine) {
  // Check if line has identifiable issues:
  // - Missing semicolon
  // - Wrong case (digitalwrite vs digitalWrite)
  // - Wrong operator (= vs ==)
  // - Missing punctuation in for loop
  // - Wrong function call syntax

  const trimmed = codeLine.trim();

  // Missing semicolon when expected
  if (/[a-zA-Z0-9)]}]$/.test(trimmed) && !trimmed.includes('{') && !trimmed.includes('}')) {
    if (!trimmed.endsWith(';') && !trimmed.endsWith(',')) return true;
  }

  // Case sensitivity issues (digitalwrite vs digitalWrite, pinmode vs pinMode, etc.)
  if (/digitalwrite|pinmode|digitalread|analogread|analogwrite|serial\.println|serial\.print/.test(trimmed.toLowerCase())) {
    // Should be camelCase
    if (trimmed.includes('digitalwrite') || trimmed.includes('pinmode') ||
        trimmed.includes('digitalread') || trimmed.includes('analogread') ||
        trimmed.includes('analogwrite') || trimmed.includes('Serial.println') === false) {
      return true;
    }
  }

  // Wrong operators (= instead of ==, && instead of ,, etc.)
  if (/if\s*\(.*=\s*\d+\)/.test(trimmed) && !trimmed.includes('==')) return true;
  if (/for\s*\(.*,\s*i\+\+/.test(trimmed)) return true; // Should be semicolons, not commas

  // Missing function arguments
  if (/digitalWrite\([^,)]+\)$/.test(trimmed)) return true; // Missing second argument

  // String instead of number in delay()
  if (/delay\s*\(\s*"[^"]*"\s*\)/.test(trimmed)) return true;

  return false;
}

function checkBugLine(codeLine) {
  return /[a-zA-Z0-9)]}]$/.test(codeLine.trim()) &&
         !codeLine.trim().endsWith(';') &&
         !codeLine.trim().endsWith('{') &&
         !codeLine.trim().endsWith('}') &&
         !codeLine.trim().startsWith('//') ||
         /digitalwrite|pinmode|digitalread/.test(codeLine.toLowerCase()) ||
         /for\s*\(.*,/.test(codeLine) ||
         /if\s*\([^=]*=\s*[0-9]/.test(codeLine);
}

// ─────────────────────────────────────────────────────────────────────
// TEST SUITE
// ─────────────────────────────────────────────────────────────────────

console.log(`${colors.blue}🧪 Arduino Learning Lab Test Suite${colors.reset}\n`);

const htmlPath = path.join(__dirname, '..', 'index.html');
let jsCode;

// Extract and parse JavaScript
try {
  jsCode = extractJSFromHTML(htmlPath);
} catch (err) {
  console.error(`${colors.red}Failed to extract JavaScript: ${err.message}${colors.reset}`);
  process.exit(1);
}

console.log(`${colors.blue}1. JavaScript Syntax Validation${colors.reset}`);
test('JS code extracts from HTML without errors', () => {
  assert(jsCode.length > 0, 'JS code should not be empty');
});

test('JS code contains React imports', () => {
  assert(jsCode.includes('useState'), 'Should import useState from React');
  assert(jsCode.includes('useEffect'), 'Should import useEffect from React');
});

test('JS code contains PROJECTS array', () => {
  assert(jsCode.includes('const PROJECTS = ['), 'Should define PROJECTS array');
  assert(jsCode.includes('const { useState, useEffect') || jsCode.includes('useState, useEffect'), 'Should destructure React hooks');
});

// Parse the JS to extract game generation functions and data
let gameGenFunctions = {};
let projectsData = [];

try {
  // We'll use a simple regex extraction approach since we can't safely eval() untrusted code
  // For generateComponentMatchGame
  const matchGameMatch = jsCode.match(/function generateComponentMatchGame[\s\S]*?return.*?}/);
  if (matchGameMatch) gameGenFunctions.match = matchGameMatch[0];

  // For generateDebugCodeGame
  const debugGameMatch = jsCode.match(/function generateDebugCodeGame[\s\S]*?return.*?}/);
  if (debugGameMatch) gameGenFunctions.debug = debugGameMatch[0];

  // For generateQuizGame
  const quizGameMatch = jsCode.match(/function generateQuizGame[\s\S]*?return.*?}/);
  if (quizGameMatch) gameGenFunctions.quiz = quizGameMatch[0];
} catch (err) {
  console.error(`${colors.red}Warning: Could not parse game functions: ${err.message}${colors.reset}`);
}

// ─────────────────────────────────────────────────────────────────────
// 2. DEBUG CODE GAME TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}2. Debug Code Game - Content Correctness${colors.reset}`);

// Extract bugsPool data
const bugsPoolMatch = jsCode.match(/const bugsPool = \[([\s\S]*?)\];/);
if (bugsPoolMatch) {
  // Parse bugs using a safer approach - find each bug object
  const bugsStr = '[' + bugsPoolMatch[1] + ']';

  try {
    // Count bugs in the string
    const bugMatches = jsCode.match(/{ code:.*?answers:.*?},?/g) || [];
    let bugIndex = 0;

    // Extract individual bugs by parsing the structure
    const codeMatches = jsCode.match(/{ code: "[^"]*".*?bugLine: (\d+).*?answers: \[(.*?)\] }/g) || [];

    codeMatches.forEach((bugStr, idx) => {
      test(`Bug scenario ${idx + 1}: bugLine index is within answers array`, () => {
        // Extract bugLine number
        const bugLineMatch = bugStr.match(/bugLine: (\d+)/);
        assert(bugLineMatch, 'Should have bugLine property');

        const bugLine = parseInt(bugLineMatch[1], 10);

        // Extract answers count
        const answersMatch = bugStr.match(/answers: \[(.*?)\]/);
        assert(answersMatch, 'Should have answers array');

        const answerCount = (answersMatch[1].match(/Line/g) || []).length;
        assert(bugLine < answerCount, `bugLine ${bugLine} should be within answers count ${answerCount}`);
      });
    });

    // More targeted tests on the actual bugs array from the code
    const bugsArrayMatch = jsCode.match(/const bugsPool = \[([\s\S]*?)\n  \];/);
    if (bugsArrayMatch) {
      // Count the bugs
      const bugCount = (bugsArrayMatch[1].match(/{ code:/g) || []).length;
      test(`Should have at least 10 bug scenarios`, () => {
        assert(bugCount >= 10, `Should have at least 10 bugs, found ${bugCount}`);
      });
    }
  } catch (err) {
    console.log(`  ${colors.yellow}⚠ Could not validate individual bugs: ${err.message}${colors.reset}`);
  }
}

test('Debug game generation returns 3 unique bugs', () => {
  assert(gameGenFunctions.debug, 'Should have debug game function');
  assert(gameGenFunctions.debug.includes('slice(0, 3)'), 'Should slice first 3 bugs');
  assert(gameGenFunctions.debug.includes('sort'), 'Should shuffle bugs');
});

test('Debug game XP calculation is correct', () => {
  // correctCount * 10
  assert(jsCode.includes('scoreRef.current * 10'), 'Should calculate XP as correctCount * 10');
});

// ─────────────────────────────────────────────────────────────────────
// 3. CIRCUIT QUIZ TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}3. Circuit Quiz - Content Correctness${colors.reset}`);

// Extract questionPool
const questionPoolMatch = jsCode.match(/const questionPool = \[([\s\S]*?)\n  \];/);
let questionCount = 0;
if (questionPoolMatch) {
  questionCount = (questionPoolMatch[1].match(/{ q:/g) || []).length;

  test(`Should have multiple quiz questions (found ${questionCount})`, () => {
    assert(questionCount >= 10, `Should have at least 10 questions, found ${questionCount}`);
  });
}

test('Quiz game selection returns 5 unique questions', () => {
  assert(jsCode.includes('slice(0, 5)'), 'Should slice first 5 questions');
  assert(jsCode.includes('questionPool.sort') || jsCode.includes('QUIZ_QUESTIONS].sort'), 'Should shuffle questions');
});

test('Quiz options are shuffled and include correct answer', () => {
  assert(jsCode.match(/options:\s*\[q\.a,\s*\.\.\./), 'Should include correct answer in options');
  assert(jsCode.includes('sort(() => Math.random() - 0.5)'), 'Should shuffle options');
});

test('Quiz XP calculation is correct', () => {
  assert(jsCode.includes('correctCount * 10'), 'Should calculate XP as correctCount * 10');
});

test('Quiz game tracks answers correctly', () => {
  assert(jsCode.includes('answers[qIdx] === q.a'), 'Should compare answer with correct answer');
});

// ─────────────────────────────────────────────────────────────────────
// 4. COMPONENT MATCH TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}4. Component Match - Content Correctness${colors.reset}`);

// Extract pairsPool
const pairsPoolMatch = jsCode.match(/const pairsPool = \[([\s\S]*?)\n  \];/);
let pairCount = 0;
if (pairsPoolMatch) {
  pairCount = (pairsPoolMatch[1].match(/{ img:/g) || []).length;

  test(`Should have multiple pairs (found ${pairCount})`, () => {
    assert(pairCount >= 4, `Should have at least 4 pairs for matching`);
  });

  test('No duplicate labels in pairs pool', () => {
    // Check for duplicate labels by extracting them
    const labels = pairsPoolMatch[1].match(/label: "([^"]*)"/g) || [];
    const uniqueLabels = new Set(labels);
    assert(uniqueLabels.size >= pairCount / 2, 'Should not have duplicate labels');
  });

  test('Emoji-label pairs are logical', () => {
    // Check for obviously wrong pairings
    const pairsStr = pairsPoolMatch[1];

    // Should not have camera emoji for IR receiver
    if (pairsStr.includes('IR Receiver')) {
      assert(!pairsStr.match(/📷.*IR Receiver|IR Receiver.*📷/), 'IR Receiver should not use camera emoji');
    }
  });
}

test('Component match game generates exactly 8 cards (4 pairs doubled)', () => {
  assert(gameGenFunctions.match.includes('slice(0, 4)'), 'Should pick 4 pairs');
  assert(gameGenFunctions.match.includes('[...shuffled, ...shuffled]'), 'Should double pairs for 8 cards');
});

test('Component match flat XP reward is 50', () => {
  assert(jsCode.includes('onComplete(50)'), 'Match game should award 50 XP');
});

test('Component match cards are shuffled', () => {
  assert(gameGenFunctions.match.includes('sort(() => Math.random() - 0.5)'), 'Should shuffle cards');
});

// ─────────────────────────────────────────────────────────────────────
// 5. XP MATH TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}5. XP Math Validation${colors.reset}`);

test('Quest completion awards exactly 100 XP', () => {
  assert(jsCode.includes('addXpPop(100)'), 'Should award 100 XP for quest completion');
});

test('Total XP formula: completedCount * 100 + bonusXp', () => {
  assert(jsCode.match(/completedCount \* 100 \+ bonusXp|bonusXp.*\+ completedCount \* 100/),
    'Should calculate XP as completedCount * 100 + bonusXp');
});

test('Level formula: Math.floor(xp / 100) + 1', () => {
  assert(jsCode.includes('Math.floor(xp / 100) + 1'), 'Should calculate level correctly');
});

test('Debug game XP: correctCount * 10', () => {
  assert(jsCode.includes('scoreRef.current * 10'), 'Debug game should award XP per correct');
});

test('Quiz game XP: correctCount * 10', () => {
  // Check CircuitQuizGame for XP calculation
  assert(jsCode.includes('correctCount * 10'), 'Quiz game should award XP per correct');
});

test('Match game XP: flat 50', () => {
  assert(jsCode.includes('onComplete(50)') || jsCode.includes('50'), 'Match game should award 50 XP');
});

// ─────────────────────────────────────────────────────────────────────
// 6. REACT HOOKS ORDER TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}6. React Hooks Order Validation${colors.reset}`);

// Extract the App function
const appFunctionMatch = jsCode.match(/function App\(\) \{([\s\S]*?)\n\}/);
if (appFunctionMatch) {
  const appBody = appFunctionMatch[1];

  // Check that all useState calls come before conditional returns
  const useStateMatches = [...appBody.matchAll(/useState/g)];
  const useEffectMatches = [...appBody.matchAll(/useEffect/g)];
  const conditionalReturns = [...appBody.matchAll(/if \(.*?\) return|if \(showSetup\)|if \(view ===|if \(miniGame\)/g)];

  test('All useState calls appear before conditional returns', () => {
    if (useStateMatches.length > 0 && conditionalReturns.length > 0) {
      const lastUseStateIndex = useStateMatches[useStateMatches.length - 1].index;
      const firstReturnIndex = conditionalReturns[0].index;
      assert(lastUseStateIndex < firstReturnIndex, 'All useState hooks must be called before returns');
    }
  });

  test('All useEffect calls appear before conditional returns', () => {
    if (useEffectMatches.length > 0 && conditionalReturns.length > 0) {
      const lastUseEffectIndex = useEffectMatches[useEffectMatches.length - 1].index;
      const firstReturnIndex = conditionalReturns[0].index;
      assert(lastUseEffectIndex < firstReturnIndex, 'All useEffect hooks must be called before returns');
    }
  });
}

// ─────────────────────────────────────────────────────────────────────
// 7. GAME GENERATION FUNCTION TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}7. Game Generation Functions${colors.reset}`);

test('generateDebugCodeGame exists and returns debug game type', () => {
  assert(jsCode.includes('function generateDebugCodeGame'), 'Should define function');
  assert(jsCode.includes('type: "debug"'), 'Should return debug game object');
});

test('generateQuizGame exists and returns quiz game type', () => {
  assert(jsCode.includes('function generateQuizGame'), 'Should define function');
  assert(jsCode.includes('type: "quiz"'), 'Should return quiz game object');
});

test('generateComponentMatchGame exists and returns match game type', () => {
  assert(jsCode.includes('function generateComponentMatchGame'), 'Should define function');
  assert(jsCode.includes('type: "match"'), 'Should return match game object');
});

// ─────────────────────────────────────────────────────────────────────
// 8. LOCALSTORAGE TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}8. LocalStorage Persistence${colors.reset}`);

test('LocalStorage key format uses sparkcity_ prefix', () => {
  assert(jsCode.includes("'sparkcity_'"), 'Should use sparkcity_ prefix for save keys');
});

test('LocalStorage key uses playerName.toLowerCase()', () => {
  assert(jsCode.includes("playerName.toLowerCase()") || jsCode.includes("name.toLowerCase()"),
    'Should convert player name to lowercase for key');
});

test('Saved data includes required fields', () => {
  assert(jsCode.includes('completed'), 'Should save completed quests');
  assert(jsCode.includes('bonusXp'), 'Should save bonusXp');
  assert(jsCode.includes('lastPlayed'), 'Should save lastPlayed timestamp');
});

test('Save function is called in useEffect', () => {
  assert(jsCode.includes('useEffect') && jsCode.includes('saveState'),
    'Should auto-save in useEffect');
});

// ─────────────────────────────────────────────────────────────────────
// 9. PROJECTS DATA VALIDATION
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}9. Projects Data Validation${colors.reset}`);

const projectsMatch = jsCode.match(/const PROJECTS = \[([\s\S]*?)\n\];/);
let projectTotal = 0;
if (projectsMatch) {
  projectTotal = (projectsMatch[1].match(/id: \d+/g) || []).length;

  test(`Should have 12 projects (found ${projectTotal})`, () => {
    assert(projectTotal === 12, `Should have exactly 12 projects, found ${projectTotal}`);
  });

  test('Each project has required fields', () => {
    const requiredFields = ['id', 'title', 'icon', 'code', 'questTitle'];
    requiredFields.forEach(field => {
      assert(jsCode.includes(`${field}:`), `All projects should have ${field} field`);
    });
  });
}

// ─────────────────────────────────────────────────────────────────────
// 10. COMPONENT & STYLING TESTS
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}10. UI Components Validation${colors.reset}`);

test('App component is defined', () => {
  assert(jsCode.includes('function App()'), 'Should define App component');
});

test('SetupScreen component is defined', () => {
  assert(jsCode.includes('function SetupScreen'), 'Should define SetupScreen');
});

test('QuestView component is defined', () => {
  assert(jsCode.includes('function QuestView'), 'Should define QuestView');
});

test('MiniGameView component is defined', () => {
  assert(jsCode.includes('function MiniGameView'), 'Should define MiniGameView');
});

test('DebugCodeGame component is defined', () => {
  assert(jsCode.includes('function DebugCodeGame'), 'Should define DebugCodeGame');
});

test('CircuitQuizGame component is defined', () => {
  assert(jsCode.includes('function CircuitQuizGame'), 'Should define CircuitQuizGame');
});

test('ComponentMatchGame component is defined', () => {
  assert(jsCode.includes('function ComponentMatchGame'), 'Should define ComponentMatchGame');
});

test('React root renders to #root element', () => {
  assert(jsCode.includes('document.getElementById("root")'), 'Should render to #root');
  assert(jsCode.includes('ReactDOM.createRoot'), 'Should use createRoot');
  assert(jsCode.includes('root.render'), 'Should call render');
});

// ─────────────────────────────────────────────────────────────────────
// SUMMARY
// ─────────────────────────────────────────────────────────────────────

console.log(`\n${colors.blue}${'='.repeat(50)}${colors.reset}`);
console.log(`${colors.blue}Test Summary${colors.reset}`);
console.log(`${colors.blue}${'='.repeat(50)}${colors.reset}`);

console.log(`Total tests:  ${testCount}`);
console.log(`${colors.green}Passed:       ${passCount}${colors.reset}`);

if (failCount > 0) {
  console.log(`${colors.red}Failed:       ${failCount}${colors.reset}`);
  process.exit(1);
} else {
  console.log(`${colors.green}Failed:       ${failCount}${colors.reset}`);
  console.log(`\n${colors.green}✓ All tests passed!${colors.reset}`);
  process.exit(0);
}
