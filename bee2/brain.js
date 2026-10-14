#!/usr/bin/env node
/**
 * mind.js — a compact, self-directed skill-discovery system.
 *
 * No API, no network, no external targets or reference answers.
 * The only objective is intrinsic: produce a behavior that has never
 * been produced before (novelty-driven exploration). This mirrors how
 * infants explore via repeated, varied motor actions and retain the
 * ones that produce a distinguishable effect (Piaget's "circular
 * reactions"), rather than being taught a fixed curriculum.
 *
 * Architecture: a small typed stack machine.
 *   - 4 typed stacks: num, str, arr, bool
 *   - "primitives" pop typed operands, push a typed result
 *   - a "program" is a sequence of primitive names
 *   - once a program is confirmed to produce novel behavior for a given
 *     input signature, it's promoted to a first-class "skill" — a new
 *     opaque primitive other programs can call, enabling composition to
 *     deepen over time.
 *
 * Six mechanisms beyond the base loop:
 *   1. A richer, multi-arity primitive set (the "reflexes")
 *   2. Varied stimuli per type, sampled across multiple scenarios
 *   3. A periodic sleep/consolidation pass (integrity check + pruning)
 *   4. True multi-input skills (arity > 1), via the stack VM
 *   5. Strategic exploration — novelty search biased away from
 *      already-well-explored (input-signature -> output-type) buckets
 *   6. Growth tracking — a persisted log of skill count over time
 *
 * Run: node mind.js
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------
const SKILLS_FILE = path.join(__dirname, "skills.json");
const TICK_MS = 3000;
const ATTEMPTS_PER_TICK = 6000;
const SLEEP_EVERY_N_TICKS = 20;
const GROWTH_LOG_CAP = 300;

const TYPES = ["num", "str", "arr", "bool"];

// ---------------------------------------------------------------------
// Stimuli — fixed reference inputs the mind is tested against.
// Not answers, just consistent "sensory input" (like a baby's toys).
// Multiple scenarios per type let multi-arg signatures see varied,
// non-repeating combinations (see scenarioValue()).
// ---------------------------------------------------------------------
const STIMULI = {
  num: [0, 1, -4, 8, -1],
  str: ["", "ab", "namaste", "duniya", "x"],
  arr: [[], [3, 1, 2], [-5, 10, 0, 7], [9], [1, 1, 2]],
  bool: [true, false, true, false, true],
};
const SCENARIO_COUNT = 5;

function scenarioValue(type, scenarioIdx, argIdx) {
  const pool = STIMULI[type];
  return pool[(scenarioIdx + argIdx) % pool.length];
}

// ---------------------------------------------------------------------
// Primitives — the fixed "reflexes". These are never learned; they are
// the body the mind explores with. Everything discovered is a
// composition of these (or of previously discovered skills).
// ---------------------------------------------------------------------
const PRIMITIVES = [
  // numeric, unary
  { name: "inc", in: ["num"], out: "num", fn: (a) => a + 1 },
  { name: "dec", in: ["num"], out: "num", fn: (a) => a - 1 },
  { name: "neg", in: ["num"], out: "num", fn: (a) => -a },
  { name: "abs", in: ["num"], out: "num", fn: (a) => Math.abs(a) },
  { name: "is_even", in: ["num"], out: "bool", fn: (a) => a % 2 === 0 },
  { name: "is_odd", in: ["num"], out: "bool", fn: (a) => a % 2 !== 0 },
  { name: "is_positive", in: ["num"], out: "bool", fn: (a) => a > 0 },
  // numeric, binary
  { name: "add", in: ["num", "num"], out: "num", fn: (a, b) => a + b },
  { name: "sub", in: ["num", "num"], out: "num", fn: (a, b) => a - b },
  { name: "mul", in: ["num", "num"], out: "num", fn: (a, b) => a * b },
  { name: "mod", in: ["num", "num"], out: "num", fn: (a, b) => (b === 0 ? 0 : a % b) },
  { name: "gt", in: ["num", "num"], out: "bool", fn: (a, b) => a > b },
  { name: "lt", in: ["num", "num"], out: "bool", fn: (a, b) => a < b },
  { name: "eq_num", in: ["num", "num"], out: "bool", fn: (a, b) => a === b },
  // array, unary
  { name: "arr_len", in: ["arr"], out: "num", fn: (a) => a.length },
  { name: "arr_sum", in: ["arr"], out: "num", fn: (a) => a.reduce((x, y) => x + y, 0) },
  { name: "arr_max", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.max(...a) : 0) },
  { name: "arr_min", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.min(...a) : 0) },
  { name: "arr_reverse", in: ["arr"], out: "arr", fn: (a) => [...a].reverse() },
  { name: "arr_sort", in: ["arr"], out: "arr", fn: (a) => [...a].sort((x, y) => x - y) },
  { name: "arr_is_empty", in: ["arr"], out: "bool", fn: (a) => a.length === 0 },
  { name: "arr_join", in: ["arr"], out: "str", fn: (a) => a.join(",") },
  // array, binary
  { name: "arr_contains", in: ["arr", "num"], out: "bool", fn: (a, n) => a.includes(n) },
  { name: "arr_push", in: ["arr", "num"], out: "arr", fn: (a, n) => [...a, n] },
  { name: "arr_index_of", in: ["arr", "num"], out: "num", fn: (a, n) => a.indexOf(n) },
  { name: "arr_concat", in: ["arr", "arr"], out: "arr", fn: (a, b) => [...a, ...b] },
  // string, unary
  { name: "str_len", in: ["str"], out: "num", fn: (a) => a.length },
  { name: "str_upper", in: ["str"], out: "str", fn: (a) => a.toUpperCase() },
  { name: "str_lower", in: ["str"], out: "str", fn: (a) => a.toLowerCase() },
  { name: "str_reverse", in: ["str"], out: "str", fn: (a) => [...a].reverse().join("") },
  { name: "str_is_empty", in: ["str"], out: "bool", fn: (a) => a.length === 0 },
  { name: "str_word_count", in: ["str"], out: "num", fn: (a) => (a.trim() ? a.trim().split(/\s+/).length : 0) },
  // string, binary
  { name: "str_concat", in: ["str", "str"], out: "str", fn: (a, b) => a + b },
  { name: "str_contains", in: ["str", "str"], out: "bool", fn: (a, b) => a.includes(b) },
  // bool
  { name: "not", in: ["bool"], out: "bool", fn: (a) => !a },
  { name: "and", in: ["bool", "bool"], out: "bool", fn: (a, b) => a && b },
  { name: "or", in: ["bool", "bool"], out: "bool", fn: (a, b) => a || b },
  { name: "xor", in: ["bool", "bool"], out: "bool", fn: (a, b) => a !== b },
];

// Which (input-signature) shapes the mind is allowed to attempt. This
// bounds the search space; it does not tell it what the *behavior*
// should be for any of them — that's still fully discovered.
const SIGNATURE_POOL = [
  ["num"], ["str"], ["arr"], ["bool"],
  ["num", "num"], ["str", "str"], ["arr", "num"], ["arr", "arr"], ["num", "bool"],
];

// ---------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------
function loadState() {
  if (!fs.existsSync(SKILLS_FILE)) {
    return { skills: [], growthLog: [], ticks: 0 };
  }
  try {
    const data = JSON.parse(fs.readFileSync(SKILLS_FILE, "utf-8"));
    return {
      skills: data.skills || [],
      growthLog: data.growthLog || [],
      ticks: data.ticks || 0,
    };
  } catch {
    return { skills: [], growthLog: [], ticks: 0 };
  }
}

function saveState(state) {
  fs.writeFileSync(SKILLS_FILE, JSON.stringify(state, null, 2), "utf-8");
}

// ---------------------------------------------------------------------
// Stack VM
// ---------------------------------------------------------------------
function execute(program, registry, seed) {
  const stacks = {
    num: [...(seed.num || [])],
    str: [...(seed.str || [])],
    arr: [...(seed.arr || [])],
    bool: [...(seed.bool || [])],
  };
  for (const opName of program) {
    const op = registry[opName];
    if (!op) return null;
    const args = [];
    for (const t of op.in) {
      if (stacks[t].length === 0) return null;
      args.push(stacks[t].pop());
    }
    let result;
    try {
      result = op.fn(...args);
    } catch {
      return null;
    }
    stacks[op.out].push(result);
  }
  return stacks;
}

function randomProgram(registry, maxLen) {
  const names = Object.keys(registry);
  const len = 1 + Math.floor(Math.random() * maxLen);
  const prog = [];
  for (let i = 0; i < len; i++) prog.push(names[Math.floor(Math.random() * names.length)]);
  return prog;
}

function makeSkillFn(skill, registry) {
  return (...args) => {
    const seed = { num: [], str: [], arr: [], bool: [] };
    skill.inputTypes.forEach((t, i) => seed[t].push(args[i]));
    const result = execute(skill.program, registry, seed);
    const outStack = result && result[skill.outputType];
    if (!outStack || outStack.length === 0) throw new Error("skill produced no output");
    return outStack[outStack.length - 1];
  };
}

function buildRegistry(skills) {
  const registry = {};
  for (const p of PRIMITIVES) registry[p.name] = p;
  for (const s of skills) {
    registry[s.name] = { name: s.name, in: s.inputTypes, out: s.outputType, fn: null };
  }
  // Second pass: skill functions close over `registry`, so forward
  // references between skills resolve fine once every entry exists.
  for (const s of skills) {
    registry[s.name].fn = makeSkillFn(s, registry);
  }
  return registry;
}

// ---------------------------------------------------------------------
// Fingerprinting — a program's observed behavior across scenarios,
// for a given input signature and output type. Two programs with the
// same fingerprint are considered the same discovery.
// ---------------------------------------------------------------------
function fingerprintFor(program, registry, inputTypes, outputType) {
  const outputs = [];
  let sample = null;
  for (let s = 0; s < SCENARIO_COUNT; s++) {
    const seed = { num: [], str: [], arr: [], bool: [] };
    const inputsUsed = [];
    inputTypes.forEach((t, i) => {
      const v = scenarioValue(t, s, i);
      seed[t].push(v);
      inputsUsed.push(v);
    });
    const result = execute(program, registry, seed);
    if (!result) return null;
    const outStack = result[outputType];
    if (outStack.length === 0) return null;
    const value = outStack[outStack.length - 1];
    outputs.push(value);
    if (s === 0) sample = { in: inputsUsed, out: value };
  }
  return { serialized: JSON.stringify(outputs), sample };
}

function bucketKey(inputTypes, outputType) {
  return `${[...inputTypes].sort().join(",")}=>${outputType}`;
}

// ---------------------------------------------------------------------
// Strategic exploration — pick which signature/output shape to try
// next, weighted away from buckets that already have many skills.
// This is the "self-observation" step: the mind looks at its own
// skill distribution before deciding where to explore.
// ---------------------------------------------------------------------
function pickTarget(skills) {
  const counts = {};
  for (const s of skills) {
    const key = bucketKey(s.inputTypes, s.outputType);
    counts[key] = (counts[key] || 0) + 1;
  }
  const candidates = [];
  for (const inputs of SIGNATURE_POOL) {
    for (const out of TYPES) {
      const key = bucketKey(inputs, out);
      candidates.push({ inputs, out, weight: 1 / (1 + (counts[key] || 0)) });
    }
  }
  const total = candidates.reduce((sum, c) => sum + c.weight, 0);
  let r = Math.random() * total;
  for (const c of candidates) {
    r -= c.weight;
    if (r <= 0) return c;
  }
  return candidates[candidates.length - 1];
}

function exploreOnce(registry, knownFingerprints, skills) {
  const { inputs, out } = pickTarget(skills);
  const maxLen = Math.min(2 + Math.floor(skills.length / 5), 6);

  for (let attempt = 0; attempt < ATTEMPTS_PER_TICK; attempt++) {
    const program = randomProgram(registry, maxLen);
    const fp = fingerprintFor(program, registry, inputs, out);
    if (!fp) continue;
    const fullKey = `${inputs.join(",")}=>${out}::${fp.serialized}`;
    if (!knownFingerprints.has(fullKey)) {
      return { program, inputTypes: inputs, outputType: out, fullKey, sample: fp.sample };
    }
  }
  return null;
}

// ---------------------------------------------------------------------
// Sleep / consolidation — periodically re-verify every stored skill
// still reproduces its fingerprint deterministically, and drop any
// that have become invalid or duplicated (defensive integrity pass,
// loosely analogous to memory consolidation during sleep).
// ---------------------------------------------------------------------
function consolidate(state) {
  const registry = buildRegistry(state.skills);
  const seen = new Set();
  const kept = [];
  for (const s of state.skills) {
    const fp = fingerprintFor(s.program, registry, s.inputTypes, s.outputType);
    if (!fp) continue; // no longer reproducible — drop
    const key = `${s.inputTypes.join(",")}=>${s.outputType}::${fp.serialized}`;
    if (seen.has(key)) continue; // duplicate — drop
    seen.add(key);
    kept.push(s);
  }
  const removed = state.skills.length - kept.length;
  state.skills = kept;

  const byOutput = {};
  for (const s of kept) byOutput[s.outputType] = (byOutput[s.outputType] || 0) + 1;
  const lengths = kept.map((s) => s.program.length);
  const maxLen = lengths.length ? Math.max(...lengths) : 0;

  console.log(
    `\n--- consolidation --- total: ${kept.length} | removed: ${removed} | by output type: ${JSON.stringify(
      byOutput
    )} | deepest program: ${maxLen} steps`
  );

  if (state.growthLog.length >= 2) {
    const recent = state.growthLog.slice(-10);
    const dtMin = (recent[recent.length - 1].t - recent[0].t) / 60000;
    const dCount = recent[recent.length - 1].total - recent[0].total;
    const rate = dtMin > 0 ? (dCount / dtMin).toFixed(2) : "n/a";
    console.log(`growth rate (last ${recent.length} discoveries): ${rate} skills/min`);
  }
  console.log("---\n");
}

// ---------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------
async function tick(state) {
  const registry = buildRegistry(state.skills);
  const knownFingerprints = new Set(
    state.skills.map((s) => {
      const fp = fingerprintFor(s.program, registry, s.inputTypes, s.outputType);
      return `${s.inputTypes.join(",")}=>${s.outputType}::${fp.serialized}`;
    })
  );

  const found = exploreOnce(registry, knownFingerprints, state.skills);
  const time = new Date().toLocaleTimeString();

  if (found) {
    const skillName = `skill_${state.skills.length + 1}_${found.inputTypes.join("_")}_to_${found.outputType}`;
    state.skills.push({
      name: skillName,
      inputTypes: found.inputTypes,
      outputType: found.outputType,
      program: found.program,
      learnedAt: new Date().toISOString(),
    });
    state.growthLog.push({ t: Date.now(), total: state.skills.length });
    if (state.growthLog.length > GROWTH_LOG_CAP) state.growthLog.shift();

    console.log(
      `[${time}] new behavior: ${skillName}\n  program: [${found.program.join(" -> ")}]\n  example: ${JSON.stringify(
        found.sample.in
      )} -> ${JSON.stringify(found.sample.out)}`
    );
    console.log(`  total skills: ${state.skills.length}\n`);
  } else {
    console.log(`[${time}] exploring... nothing new this tick. total skills: ${state.skills.length}`);
  }

  state.ticks++;
  if (state.ticks % SLEEP_EVERY_N_TICKS === 0) {
    consolidate(state);
  }

  saveState(state);
}

async function runForever() {
  console.log(
    "Mind online. No targets, no reference answers — only intrinsic novelty-seeking.\n" +
      "Objective: do something that has not been done before.\n"
  );
  const state = loadState();
  while (true) {
    await tick(state);
    await new Promise((resolve) => setTimeout(resolve, TICK_MS));
  }
}

runForever();
