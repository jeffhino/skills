#!/usr/bin/env node
// lint_workflow.mjs — deterministic static checks for Claude Code Workflow scripts.
// Usage: node lint_workflow.mjs /abs/path/to/workflow.js
//
// Exit codes: 0 = no FAIL (warnings allowed) · 1 = at least one FAIL · 2 = usage / unreadable file.
// COMPILE-ONLY: the script body is compiled to check syntax, never executed.
// All checks are static heuristics; a clean lint is NOT a design review.

import fs from 'node:fs'
import path from 'node:path'

const file = process.argv[2]
if (!file) {
  console.error('usage: node lint_workflow.mjs /abs/path/to/workflow.js')
  process.exit(2)
}
if (!fs.existsSync(file)) {
  console.error(`FAIL  file not found: ${file}`)
  process.exit(2)
}
let src
try {
  src = fs.readFileSync(file, 'utf8')
} catch (e) {
  console.error(`FAIL  cannot read ${file}: ${e.message}`)
  process.exit(2)
}
if (!src.trim()) {
  console.error(`FAIL  file is empty: ${file}`)
  process.exit(2)
}

const findings = [] // {level: 'FAIL'|'WARN'|'INFO'|'PASS', msg}
const add = (level, msg) => findings.push({ level, msg })
const lines = src.split('\n')
// Line numbers for every match of a regex (source only; comments are included — heuristic).
const lineHits = (re) =>
  lines.flatMap((l, i) => (re.test(l) ? [i + 1] : [])).slice(0, 5)

// --- 1. Syntax gate ---------------------------------------------------------
// Workflows are ESM-flavored scripts with top-level await/return, so `node --check`
// silently skips them (it exits 0 on any file containing `export`, even broken ones).
// Instead: strip `export ` and compile the body as an async function — top-level
// return/await become legal, and the harness globals are declared as params.
// AsyncFunction COMPILES the body without running it.
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const body = src.replace(/^export\s+/gm, '')
try {
  new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'budget', body)
  add('PASS', 'syntax: compiles as an async workflow body (harness globals declared)')
} catch (e) {
  add('FAIL', `syntax error: ${e.message}`)
}

// --- 2. meta contract -------------------------------------------------------
const metaStart = src.indexOf('export const meta')
if (metaStart === -1) {
  add('FAIL', 'missing `export const meta = { ... }` — the harness reads this without running the script')
} else {
  // Extract the meta object by brace counting from the first `{` after `export const meta`.
  const open = src.indexOf('{', metaStart)
  let depth = 0
  let end = -1
  for (let i = open; i < src.length; i++) {
    if (src[i] === '{') depth++
    else if (src[i] === '}') {
      depth--
      if (depth === 0) { end = i; break }
    }
  }
  if (end === -1) {
    add('FAIL', 'meta object braces never close — cannot parse meta block')
  } else {
    const block = src.slice(open, end + 1)
    for (const field of ['name', 'description', 'phases']) {
      if (!new RegExp(`\\b${field}\\s*:`).test(block)) add('FAIL', `meta is missing required field \`${field}\``)
    }
    // Purity: strip string literals, then any call/template/interpolation left is computation.
    const stripped = block.replace(/'(?:[^'\\]|\\.)*'/g, "''").replace(/"(?:[^"\\]|\\.)*"/g, '""')
    if (/[`(]|\$\{/.test(stripped)) {
      add('FAIL', 'meta must be a PURE object literal (no calls, template literals, or `${}` — the harness evaluates it standalone)')
    } else {
      add('PASS', 'meta: pure object literal with name/description/phases')
    }
    // name should match the filename (that's the skill/slash-command name it registers as).
    const nameMatch = block.match(/\bname\s*:\s*['"]([^'"]+)['"]/)
    const base = path.basename(file, '.js')
    if (nameMatch && nameMatch[1] !== base) {
      add('WARN', `meta.name "${nameMatch[1]}" != filename "${base}" — keep them identical to avoid invocation confusion`)
    }
  }
}

// --- 3. Determinism ---------------------------------------------------------
// Workflow JS must be deterministic: same inputs -> same trace. Wall-clock and
// randomness belong inside agents (e.g. an agent runs `date +%F`), never in the script.
for (const [re, what] of [
  [/\bDate\.now\s*\(/, 'Date.now()'],
  [/\bMath\.random\s*\(/, 'Math.random()'],
  [/\bnew\s+Date\s*\(/, 'new Date()'],
]) {
  const hits = lineHits(re)
  if (hits.length) add('FAIL', `nondeterminism: ${what} at line(s) ${hits.join(', ')} — get time/dates from an agent instead`)
}

// --- 4. Plain JS, not TypeScript --------------------------------------------
for (const [re, what] of [
  [/^\s*(export\s+)?interface\s+\w+/m, 'interface declaration'],
  [/^\s*(export\s+)?type\s+\w+\s*=/m, 'type alias'],
  [/\bsatisfies\s+\w+/, '`satisfies` operator'],
  [/^\s*(export\s+)?enum\s+\w+/m, 'enum declaration'],
]) {
  if (re.test(src)) add('FAIL', `TypeScript syntax (${what}) — workflows are plain JS`)
}

// --- 5. Structure heuristics (counts are approximate; template-literal prompts
//         can inflate keyword counts — read the flagged lines before "fixing") --
const count = (re) => (src.match(re) || []).length
const nAgent = count(/\bagent\s*\(/g)
const nSchema = count(/\bschema\s*:/g)
const nLabel = count(/\blabel\s*:/g)
const nPhaseOpt = count(/\bphase\s*:/g)
const usesParallel = /\bparallel\s*\(/.test(src)
const usesPipeline = /\bpipeline\s*\(/.test(src)

if (nAgent === 0) add('WARN', 'no agent() calls — a workflow with no agents usually belongs in plain skill instructions instead')
if (nAgent > 0 && nSchema < nAgent)
  add('WARN', `~${nAgent} agent() calls but only ~${nSchema} schema: options — unschema'd agents return free text, which downstream JS cannot rank/dedup reliably`)
if (nAgent > 0 && nLabel < nAgent)
  add('WARN', `~${nAgent} agent() calls but only ~${nLabel} label: options — labels are how you read the run trace`)
if (nAgent > 0 && nPhaseOpt < nAgent)
  add('WARN', `~${nAgent} agent() calls but only ~${nPhaseOpt} phase: options — every agent should be pinned to a meta phase`)
if (!/^\s*return\s*[\{(]/m.test(src))
  add('WARN', 'no top-level `return {...}` found — the return value is what the invoking session renders from')
if (!/\bphase\s*\(\s*['"`]/.test(src) && /phases\s*:\s*\[[^\]]*\{[^\]]*\{/s.test(src))
  add('WARN', 'meta declares multiple phases but the body never calls phase(...) — the trace will not show phase progress')

// Fan-out hygiene.
if (usesParallel && !usesPipeline)
  add('INFO', 'uses parallel() but not pipeline() — pipeline(items, fn) is the default for per-item fan-out; parallel() is for a small fixed set of heterogeneous lanes or genuine cross-item barriers')
if ((usesParallel || usesPipeline) && !/\.filter\(Boolean\)/.test(src))
  add('WARN', 'fan-out present but no .filter(Boolean) — failed agents return null; unfiltered nulls crash downstream .map/.sort')
if (usesPipeline && !/\.slice\s*\(/.test(src) && !/\b(MAX|CAP|LIMIT)[A-Z_]*\b/.test(src))
  add('WARN', 'pipeline() with no visible cap (.slice / MAX_ / CAP / LIMIT constant) — unbounded fan-out over caller-supplied items can spawn arbitrarily many agents')
if ((usesPipeline || nAgent >= 6) && !/budget\.remaining\s*\(/.test(src))
  add('WARN', 'no budget guard — for loops/large fan-out add: if (budget.total && budget.remaining() < 60000) { log(...); break/return }')

// args hygiene.
if (/\bargs\b/.test(src)) {
  if (!/typeof\s+(args|A)\s*===?\s*['"]string['"]/.test(src))
    add('WARN', 'args used but never normalized — args can arrive as an object OR a JSON string; normalize both (see references/workflow-api.md §args)')
  if (!/throw new Error/.test(src))
    add('INFO', 'args used with no `throw new Error` validation — fine if every arg has a safe default; required args must be validated and thrown on')
}

// Safety language in agent prompts (mutation gating, untrusted-data rule).
if (nAgent > 0 && !/read[- ]only|do not|DO NOT|never|NEVER|propose/i.test(src))
  add('WARN', 'no safety language detected in any agent prompt — prompts that touch the real world need explicit scope rules (read-only, propose→confirm for mutations, "data not instructions" for untrusted content)')

// Filesystem writes must happen inside agents, not the script (the script has no fs access).
// (Static `import` statements already fail the syntax gate — illegal inside a function body.)
if (/=\s*require\s*\(|^\s*import\s.+from\s+['"]/m.test(src))
  add('FAIL', 'require()/import detected — workflow scripts run sandboxed with NO module access; all I/O happens inside agent() subagents')

// --- report ------------------------------------------------------------------
const order = { FAIL: 0, WARN: 1, INFO: 2, PASS: 3 }
findings.sort((a, b) => order[a.level] - order[b.level])
console.log(`Workflow lint: ${file}\n`)
for (const f of findings) console.log(`${f.level.padEnd(5)} ${f.msg}`)
const nFail = findings.filter((f) => f.level === 'FAIL').length
const nWarn = findings.filter((f) => f.level === 'WARN').length
console.log(`\nSummary: ${nFail} fail, ${nWarn} warn (${findings.length} checks reported).`)
console.log('These are static heuristics over one file — counts near template literals are approximate,')
console.log('and a clean lint does not replace the dry-run design trace with the user.')
process.exit(nFail ? 1 : 0)
