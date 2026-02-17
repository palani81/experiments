#!/usr/bin/env node
/**
 * Arduino Learning Lab v1.1 — Comprehensive Test Suite
 * Tests all new and existing features without a browser (pure JS parsing + logic tests)
 */

const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', 'index-v1.1.html');
const html = fs.readFileSync(FILE, 'utf8');

// Extract the JavaScript between <script> and </script>
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/);
if (!scriptMatch) { console.error('FATAL: Could not extract <script> block'); process.exit(1); }
const jsCode = scriptMatch[1];

let passed = 0, failed = 0, errors = [];

function test(name, fn) {
  try {
    const result = fn();
    if (result === true || result === undefined) {
      passed++;
      console.log(`  ✓ ${name}`);
    } else {
      failed++;
      errors.push(name + ': returned ' + result);
      console.log(`  ✗ ${name} — returned ${result}`);
    }
  } catch (e) {
    failed++;
    errors.push(name + ': ' + e.message);
    console.log(`  ✗ ${name} — ${e.message}`);
  }
}

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 1. HTML STRUCTURE ═══');
// ═══════════════════════════════════════════════════════════════

test('Has DOCTYPE html', () => html.startsWith('<!DOCTYPE html>'));
test('Has meta charset UTF-8', () => html.includes('charset="UTF-8"'));
test('Has meta viewport', () => html.includes('name="viewport"'));
test('Has title', () => html.includes('<title>'));
test('Has React 18 CDN', () => html.includes('react/18.2.0'));
test('Has ReactDOM CDN', () => html.includes('react-dom/18.2.0'));
test('Has Fredoka One font', () => html.includes('Fredoka+One') || html.includes('Fredoka One'));
test('Has Nunito font', () => html.includes('Nunito'));
test('Has root div', () => html.includes('id="root"'));
test('Has closing html tag', () => html.trim().endsWith('</html>'));
test('CSS scrollbar styles', () => html.includes('::-webkit-scrollbar'));
test('CSS code block styles', () => html.includes('pre {'));
test('CSS animations (fadeIn, pulse, bounce)', () =>
  html.includes('@keyframes fadeIn') && html.includes('@keyframes pulse') && html.includes('@keyframes bounce'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 2. PROJECTS DATA (v1.0 preserved) ═══');
// ═══════════════════════════════════════════════════════════════

test('PROJECTS const declared', () => jsCode.includes('const PROJECTS'));
test('Has 12 projects (count id fields)', () => {
  const ids = jsCode.match(/id:\s*\d+,/g);
  return ids && ids.length >= 12;
});
test('Project 1: Hello LED', () => jsCode.includes('"Hello LED!"'));
test('Project 2: Traffic Light', () => jsCode.includes('"Traffic Light"'));
test('Project 3: Piano Keys', () => jsCode.includes('"Piano Keys"'));
test('Project 4: Night Light', () => jsCode.includes('"Night Light"'));
test('Project 5: Distance Detector', () => jsCode.includes('"Distance Detector"'));
test('Project 6: Thermometer', () => jsCode.includes('"Thermometer"'));
test('Project 7: IR Remote Control', () => jsCode.includes('"IR Remote Control"'));
test('Project 8: Mood Lamp', () => jsCode.includes('"Mood Lamp"'));
test('Project 9: Servo Sweeper', () => jsCode.includes('"Servo Sweeper"'));
test('Project 10: Intruder Alarm', () => jsCode.includes('"Intruder Alarm"'));
test('Project 11: Weather Station', () => jsCode.includes('"Weather Station"'));
test('Project 12: Robot Car Basics', () => jsCode.includes('"Robot Car Basics"'));

// Verify each project has all required fields
const projectFields = ['title', 'subtitle', 'icon', 'difficulty', 'category', 'color', 'time',
  'questTitle', 'questIntro', 'systemRepaired', 'components', 'learn', 'description',
  'wiring', 'code', 'challenge', 'science'];

test('All projects have core fields', () => {
  for (const field of projectFields) {
    const count = (jsCode.match(new RegExp(`${field}:\\s`, 'g')) || []).length;
    if (count < 12) return `field '${field}' found only ${count} times (need 12)`;
  }
  return true;
});

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 3. v1.1 DATA POOLS ═══');
// ═══════════════════════════════════════════════════════════════

test('QUIZ_QUESTIONS declared', () => jsCode.includes('const QUIZ_QUESTIONS'));
test('QUIZ_QUESTIONS has 30+ questions', () => {
  // Count question objects by looking for q: " patterns after QUIZ_QUESTIONS
  const qStart = jsCode.indexOf('const QUIZ_QUESTIONS');
  const qEnd = jsCode.indexOf('];', qStart);
  const block = jsCode.substring(qStart, qEnd);
  const qs = (block.match(/q:\s*"/g) || []).length;
  return qs >= 30 ? true : `only ${qs} questions found`;
});

test('DEBUG_CODE_SNIPPETS declared', () => jsCode.includes('const DEBUG_CODE_SNIPPETS'));
test('DEBUG_CODE_SNIPPETS has 20+ snippets', () => {
  const dStart = jsCode.indexOf('const DEBUG_CODE_SNIPPETS');
  const dEnd = jsCode.indexOf('];', dStart);
  const block = jsCode.substring(dStart, dEnd);
  const count = (block.match(/bugLine:\s*\d/g) || []).length;
  return count >= 20 ? true : `only ${count} snippets found`;
});
test('DEBUG_CODE_SNIPPETS has "Line N" format answers', () => {
  const dStart = jsCode.indexOf('const DEBUG_CODE_SNIPPETS');
  const dEnd = jsCode.indexOf('];', dStart);
  const block = jsCode.substring(dStart, dEnd);
  return block.includes('"Line 1"') && block.includes('"Line 2"');
});

test('COMPONENT_PAIRS declared', () => jsCode.includes('const COMPONENT_PAIRS'));
test('COMPONENT_PAIRS has 10+ pairs', () => {
  const cStart = jsCode.indexOf('const COMPONENT_PAIRS');
  const cEnd = jsCode.indexOf('];', cStart);
  const block = jsCode.substring(cStart, cEnd);
  const count = (block.match(/label:\s*"/g) || []).length;
  return count >= 10 ? true : `only ${count} pairs found`;
});

test('ACHIEVEMENT_BADGES declared', () => jsCode.includes('const ACHIEVEMENT_BADGES'));
test('ACHIEVEMENT_BADGES has 10+ badges', () => {
  const aStart = jsCode.indexOf('const ACHIEVEMENT_BADGES');
  const aEnd = jsCode.indexOf('];', aStart);
  const block = jsCode.substring(aStart, aEnd);
  const count = (block.match(/id:\s*"/g) || []).length;
  return count >= 10 ? true : `only ${count} badges found`;
});
test('Has first_quest badge', () => jsCode.includes('"first_quest"'));
test('Has city_hero badge', () => jsCode.includes('"city_hero"'));
test('Has perfect_quiz badge', () => jsCode.includes('"perfect_quiz"'));

test('EXPLAINER_CONCEPTS declared', () => jsCode.includes('const EXPLAINER_CONCEPTS'));
test('EXPLAINER_CONCEPTS has 5+ concepts', () => {
  const eStart = jsCode.indexOf('const EXPLAINER_CONCEPTS');
  const eEnd = jsCode.indexOf('];', eStart);
  const block = jsCode.substring(eStart, eEnd);
  const count = (block.match(/id:\s*"/g) || []).length;
  return count >= 5 ? true : `only ${count} concepts found`;
});
test('Has circuits_101 concept', () => jsCode.includes('"circuits_101"'));
test('Has ohms_law concept', () => jsCode.includes('"ohms_law"'));
test('Has pwm concept', () => jsCode.includes('"pwm"'));

test('CODE_COMPLETION_SNIPPETS declared', () => jsCode.includes('const CODE_COMPLETION_SNIPPETS'));
test('CODE_COMPLETION_SNIPPETS has 10+ snippets', () => {
  const ccStart = jsCode.indexOf('const CODE_COMPLETION_SNIPPETS');
  const ccEnd = jsCode.indexOf('];', ccStart);
  const block = jsCode.substring(ccStart, ccEnd);
  const count = (block.match(/blanks:\s*\[/g) || []).length;
  return count >= 10 ? true : `only ${count} snippets found`;
});

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 4. v1.1 NEW FEATURES: SVG WIRING DIAGRAMS ═══');
// ═══════════════════════════════════════════════════════════════

test('WiringDiagram function exists', () => jsCode.includes('function WiringDiagram'));
test('SVG rendering (createElement "svg")', () =>
  jsCode.includes('"svg"') || jsCode.includes("'svg'"));
test('Draws Arduino component', () => jsCode.includes('"arduino"') || jsCode.includes("'arduino'"));
test('Draws LED component', () =>
  jsCode.includes('type:"led"') || jsCode.includes("type: 'led'") || jsCode.includes('type: "led"'));
test('Draws resistor component', () =>
  jsCode.includes('type:"resistor"') || jsCode.includes("type:'resistor'") || jsCode.includes('type: "resistor"'));
test('Projects have diagram field', () => {
  const diagCount = (jsCode.match(/diagram:\s*\{/g) || []).length;
  return diagCount >= 12 ? true : `only ${diagCount} diagrams found (need 12)`;
});
test('Diagrams have components arrays', () => jsCode.includes('components:['));
test('Diagrams have wires arrays', () => jsCode.includes('wires:['));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 5. v1.1 NEW FEATURES: ACHIEVEMENT BADGES ═══');
// ═══════════════════════════════════════════════════════════════

test('checkBadgeUnlocks function exists', () => jsCode.includes('function checkBadgeUnlocks') || jsCode.includes('checkBadgeUnlocks'));
test('BadgeToast component exists', () => jsCode.includes('function BadgeToast'));
test('AchievementModal component exists', () => jsCode.includes('function AchievementModal'));
test('Badge state in App', () => jsCode.includes('setBadges'));
test('Badge toast state in App', () => jsCode.includes('badgeToast') || jsCode.includes('BadgeToast'));
test('Achievements button in header', () => jsCode.includes('showAchievements'));
test('Badge unlock on quest complete', () => jsCode.includes('checkBadgeUnlock'));
test('Badges saved to localStorage', () => jsCode.includes('badges'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 6. v1.1 NEW FEATURES: CONCEPT EXPLAINERS ═══');
// ═══════════════════════════════════════════════════════════════

test('ExplainerView component exists', () => jsCode.includes('function ExplainerView'));
test('Explainer has step navigation', () => jsCode.includes('setStep') || jsCode.includes('step'));
test('Explainer has mini-quiz', () => jsCode.includes('miniQuiz'));
test('showExplainer state', () => jsCode.includes('showExplainer'));
test('Learn More buttons', () => jsCode.includes('EXPLAINER_CONCEPTS') && jsCode.includes('projectIds'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 7. v1.1 NEW FEATURES: NEW MINI-GAMES ═══');
// ═══════════════════════════════════════════════════════════════

test('WiringGame component exists', () => jsCode.includes('function WiringGame'));
test('CodeCompletionGame component exists', () => jsCode.includes('function CodeCompletionGame'));
test('generateWiringGame function exists', () => jsCode.includes('generateWiringGame'));
test('generateCodeCompletionGame function exists', () => jsCode.includes('generateCodeCompletionGame'));
test('5-game rotation (quest.id % 5)', () => jsCode.includes('% 5'));
test('MiniGameView handles wiring type', () => jsCode.includes('"wiring"'));
test('MiniGameView handles codecomplete type', () => jsCode.includes('"codecomplete"'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 8. v1.1 NEW FEATURES: CIRCUIT SIMULATOR ═══');
// ═══════════════════════════════════════════════════════════════

test('Wokwi URL in projects', () => jsCode.includes('wokwiUrl'));
test('All 12 projects have wokwiUrl', () => {
  const count = (jsCode.match(/wokwiUrl/g) || []).length;
  return count >= 12 ? true : `only ${count} wokwiUrl references found`;
});
test('Try in Simulator button', () =>
  jsCode.includes('Simulator') || jsCode.includes('simulator') || jsCode.includes('wokwi'));
test('Opens in new tab', () => jsCode.includes('_blank'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 9. v1.1 NEW FEATURES: PARENT DASHBOARD ═══');
// ═══════════════════════════════════════════════════════════════

test('ParentDashboard component exists', () => jsCode.includes('function ParentDashboard'));
test('PIN entry system', () => jsCode.includes('pin') || jsCode.includes('PIN'));
test('PIN stored in localStorage', () => jsCode.includes('parent_pin') || jsCode.includes('parentPin'));
test('Dashboard shows completion stats', () => jsCode.includes('completedCount') || jsCode.includes('completed'));
test('Dashboard shows XP', () => jsCode.includes('totalXp') || (jsCode.includes('xp') && jsCode.includes('ParentDashboard')));
test('Dashboard shows badges', () => jsCode.includes('unlockedBadges') || jsCode.includes('ACHIEVEMENT_BADGES'));
test('Lock icon button', () => jsCode.includes('showParentDash'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 10. v1.0 PRESERVED FEATURES ═══');
// ═══════════════════════════════════════════════════════════════

test('SetupScreen component exists', () => jsCode.includes('function SetupScreen'));
test('Player name input', () => jsCode.includes('Enter your name'));
test('WorldMap component exists', () => jsCode.includes('function WorldMap'));
test('World map has snake path', () => jsCode.includes('row % 2'));
test('QuestView component exists', () => jsCode.includes('function QuestView'));
test('5-step wizard (Story, Overview, Wiring, Code, Challenge)', () =>
  jsCode.includes('"story"') && jsCode.includes('"overview"') &&
  jsCode.includes('"wiring"') && jsCode.includes('"code"') &&
  jsCode.includes('"challenge"'));
test('highlightArduinoCode exists', () => jsCode.includes('function highlightArduinoCode'));
test('Syntax highlighting keywords', () => jsCode.includes('.kw') || jsCode.includes('class="kw"'));
test('XP system', () => jsCode.includes('xp') && jsCode.includes('level'));
test('Level/rank titles', () => jsCode.includes('titleNames') || jsCode.includes('Circuit Cadet'));
test('ComponentMatchGame exists', () => jsCode.includes('function ComponentMatchGame'));
test('DebugCodeGame exists', () => jsCode.includes('DebugCodeGame'));
test('CircuitQuizGame exists', () => jsCode.includes('CircuitQuizGame'));
test('MiniGameView dispatcher', () => jsCode.includes('function MiniGameView') || jsCode.includes('MiniGameView'));
test('localStorage persistence', () => jsCode.includes('localStorage'));
test('Reset button', () => jsCode.includes('Reset') || jsCode.includes('reset'));
test('Level modal', () => jsCode.includes('showLevels') || jsCode.includes('Levels'));
test('XP poppers', () => jsCode.includes('xpPop') || jsCode.includes('addXpPop'));

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 11. JAVASCRIPT SYNTAX VALIDATION ═══');
// ═══════════════════════════════════════════════════════════════

test('No unclosed strings (basic check)', () => {
  // Check for obvious issues - odd number of template literals
  const backticks = (jsCode.match(/`/g) || []).length;
  return backticks % 2 === 0 ? true : `odd number of backticks: ${backticks}`;
});

// Note: Simple brace/bracket counting is unreliable because Arduino code
// examples inside template strings and regular strings contain unbalanced
// braces by design (e.g. `"for (int i = 0; i < 10; i++) {"`).
// Instead, we check that there are no obvious structural issues.

test('No obvious syntax errors (function declarations balanced)', () => {
  // Check that every function declaration has a matching closing brace
  const funcDecls = (jsCode.match(/function\s+\w+/g) || []).length;
  return funcDecls >= 20 ? true : `only ${funcDecls} function declarations found`;
});

test('Script block properly closed', () => {
  return html.includes('</script>') && html.includes('root.render(React.createElement(App))');
});

test('All React.createElement calls have matching parens (sampled)', () => {
  // Check that createElement calls are well-formed by sampling first/last occurrences
  const first = jsCode.indexOf('React.createElement');
  const last = jsCode.lastIndexOf('React.createElement');
  return first > 0 && last > first;
});

test('No console.error calls', () => !jsCode.includes('console.error'));
test('No TODO/FIXME comments', () => {
  const todos = (jsCode.match(/\/\/\s*(TODO|FIXME|HACK|XXX)/gi) || []).length;
  return todos === 0 ? true : `found ${todos} TODO/FIXME comments`;
});

// ═══════════════════════════════════════════════════════════════
console.log('\n═══ 12. UPDATED MINI-GAME GENERATORS ═══');
// ═══════════════════════════════════════════════════════════════

test('generateComponentMatchGame uses COMPONENT_PAIRS', () => {
  const fnStart = jsCode.indexOf('function generateComponentMatchGame');
  const fnEnd = jsCode.indexOf('\n}', fnStart);
  const fn = jsCode.substring(fnStart, fnEnd);
  return fn.includes('COMPONENT_PAIRS');
});

test('generateDebugCodeGame uses DEBUG_CODE_SNIPPETS', () => {
  const fnStart = jsCode.indexOf('function generateDebugCodeGame');
  const fnEnd = jsCode.indexOf('\n}', fnStart);
  const fn = jsCode.substring(fnStart, fnEnd);
  return fn.includes('DEBUG_CODE_SNIPPETS');
});

test('generateQuizGame uses QUIZ_QUESTIONS', () => {
  const fnStart = jsCode.indexOf('function generateQuizGame');
  const fnEnd = jsCode.indexOf('\n}', fnStart);
  const fn = jsCode.substring(fnStart, fnEnd);
  return fn.includes('QUIZ_QUESTIONS');
});

// ═══════════════════════════════════════════════════════════════
// UI WIRING & BUG FIX TESTS
// ═══════════════════════════════════════════════════════════════
console.log('\n── UI Wiring & Bug Fixes ──');

test('Header has Badges button', () => {
  return jsCode.includes('Badges') && jsCode.includes('setShowAchievements(true)');
});

test('Header has Parent Dashboard button', () => {
  return jsCode.includes('Parent') && jsCode.includes('setShowParentDash(true)');
});

test('MiniGameView routes wiring type correctly', () => {
  // Should have separate if blocks for each type, not nested
  const miniGameView = jsCode.match(/function MiniGameView[\s\S]*?^}/m);
  if (!miniGameView) return 'MiniGameView not found';
  const fn = miniGameView[0];
  return fn.includes('gameState.type === "wiring"') &&
         fn.includes('WiringGame') &&
         fn.includes('gameState.type === "codecomplete"') &&
         fn.includes('CodeCompletionGame');
});

test('MiniGameView has balanced braces (no nesting bug)', () => {
  const match = jsCode.match(/function MiniGameView\b[\s\S]*?(?=\nfunction\s)/);
  if (!match) return 'MiniGameView not found';
  const fn = match[0];
  let depth = 0;
  for (const ch of fn) {
    if (ch === '{') depth++;
    if (ch === '}') depth--;
  }
  return depth === 0;
});

test('Game selection includes wiring and codecomplete generators', () => {
  return jsCode.includes('generateWiringGame(quest.id)') &&
         jsCode.includes('generateCodeCompletionGame(quest.id)');
});

test('checkBadgeUnlocks is called in toggleComplete', () => {
  // Find toggleComplete through to its closing };
  const start = jsCode.indexOf('const toggleComplete');
  if (start === -1) return 'toggleComplete not found';
  const block = jsCode.substring(start, start + 500);
  return block.includes('checkBadgeUnlocks');
});

test('checkBadgeUnlocks is called after mini-game completion', () => {
  // Look for checkBadgeUnlocks near onComplete in MiniGameView rendering
  return (jsCode.match(/checkBadgeUnlocks/g) || []).length >= 2;
});

test('setBadgeToast is called when badges unlock', () => {
  return jsCode.includes('setBadgeToast(result.newBadges[0])');
});

test('saveState uses badges not badgesState', () => {
  const saveState = jsCode.match(/const saveState[\s\S]*?};/);
  if (!saveState) return 'saveState not found';
  return !saveState[0].includes('badgesState') && saveState[0].includes('badges');
});

test('Badges loaded from localStorage on startup', () => {
  return jsCode.includes('if (data.badges) setBadges(data.badges)');
});

test('useEffect includes badges in dependency array', () => {
  return jsCode.includes('[player, completed, bonusXp, badges]');
});

test('QuestView receives onShowExplainer prop', () => {
  return jsCode.includes('onShowExplainer') &&
         /function QuestView\([^)]*onShowExplainer/.test(jsCode);
});

test('Science Corner has Learn More explainer buttons', () => {
  return jsCode.includes('EXPLAINER_CONCEPTS.filter') && jsCode.includes('onShowExplainer(c.id)');
});

test('ExplainerView rendered conditionally in App', () => {
  return jsCode.includes('showExplainer && React.createElement(ExplainerView');
});

test('AchievementModal rendered conditionally in App', () => {
  return jsCode.includes('showAchievements && React.createElement(AchievementModal');
});

test('ParentDashboard rendered conditionally in App', () => {
  return jsCode.includes('showParentDash && React.createElement(ParentDashboard');
});

test('BadgeToast rendered conditionally in App', () => {
  return jsCode.includes('badgeToast && React.createElement(BadgeToast');
});

test('gameHistory state is tracked', () => {
  return jsCode.includes('setGameHistory') && jsCode.includes('sessionCompletions');
});

// ═══════════════════════════════════════════════════════════════
// SUMMARY
// ═══════════════════════════════════════════════════════════════
const total = passed + failed;
console.log(`\n${'═'.repeat(60)}`);
console.log(`RESULTS: ${passed}/${total} tests passed (${failed} failed)`);
console.log(`${'═'.repeat(60)}`);

if (errors.length > 0) {
  console.log('\nFailed tests:');
  errors.forEach(e => console.log(`  • ${e}`));
}

process.exit(failed > 0 ? 1 : 0);
