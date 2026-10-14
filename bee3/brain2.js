#!/usr/bin/env node
/**
 * mind2.js — mind.js + three brain-like mechanisms:
 *
 *   1. PREDICTION-BASED CURIOSITY
 *      Each (input-signature -> output-type) bucket keeps a running
 *      mean/variance of a cheap output feature. Candidate programs are
 *      first cheaply screened (1 scenario) and scored by how much they
 *      SURPRISE that running prediction (z-score). Only the most
 *      surprising candidates get the expensive full (5-scenario)
 *      fingerprint + promotion check — attention follows prediction
 *      error, not uniform brute force.
 *
 *   2. SIMILARITY-AWARE NOVELTY (fuzzy, not exact-match)
 *      Instead of "different iff not byte-identical fingerprint",
 *      a candidate is only promoted if it's behaviorally far enough
 *      (a type-appropriate distance) from every existing skill in its
 *      bucket. Near-duplicates are treated as the *same* discovery
 *      (generalization) instead of bloating skill count.
 *
 *   3. UTILITY-BASED FORGETTING
 *      Skills track how many other kept skills depend on them
 *      (are called inside their program). When the skill population
 *      exceeds a cap, the least useful *and* undepended-on ("leaf")
 *      skills are forgotten first, oldest/least-composed leaving
 *      first — bounded memory instead of unbounded accumulation.
 *
 * Run: node mind2.js [--ticks=N] [--quiet]
 *   --ticks=N   stop after N ticks (default: run forever)
 *   --quiet     suppress per-tick "nothing new" spam
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------
const argv = process.argv.slice(2);
const TICK_LIMIT = (() => {
  const a = argv.find((x) => x.startsWith("--ticks="));
  return a ? parseInt(a.split("=")[1], 10) : Infinity;
})();
const QUIET = argv.includes("--quiet");

// ---------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------
const SKILLS_FILE = path.join(__dirname, "skills2.json");
const TICK_MS = 50;
const SLEEP_EVERY_N_TICKS = 20;
const GROWTH_LOG_CAP = 300;

const MAX_ATTEMPTS_PER_TICK = 4000; // total candidate programs generated
const BATCH_SIZE = 200;             // candidates per cheap-screen batch
const ATTEND_PER_BATCH = 5;         // how many surprising ones get full attention

const SIMILARITY_THRESHOLD = 0.12;  // below this distance to nearest existing skill => "not novel enough"
const MAX_SKILLS = 220;             // bounded population; triggers forgetting above this

const TYPES = ["num", "str", "arr", "bool"];

// ---------------------------------------------------------------------
// Stimuli
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
// Primitives
// ---------------------------------------------------------------------
const PRIMITIVES = [
  { name: "inc", in: ["num"], out: "num", fn: (a) => a + 1 },
  { name: "dec", in: ["num"], out: "num", fn: (a) => a - 1 },
  { name: "neg", in: ["num"], out: "num", fn: (a) => -a },
  { name: "abs", in: ["num"], out: "num", fn: (a) => Math.abs(a) },
  { name: "is_even", in: ["num"], out: "bool", fn: (a) => a % 2 === 0 },
  { name: "is_odd", in: ["num"], out: "bool", fn: (a) => a % 2 !== 0 },
  { name: "is_positive", in: ["num"], out: "bool", fn: (a) => a > 0 },
  { name: "add", in: ["num", "num"], out: "num", fn: (a, b) => a + b },
  { name: "sub", in: ["num", "num"], out: "num", fn: (a, b) => a - b },
  { name: "mul", in: ["num", "num"], out: "num", fn: (a, b) => a * b },
  { name: "mod", in: ["num", "num"], out: "num", fn: (a, b) => (b === 0 ? 0 : a % b) },
  { name: "gt", in: ["num", "num"], out: "bool", fn: (a, b) => a > b },
  { name: "lt", in: ["num", "num"], out: "bool", fn: (a, b) => a < b },
  { name: "eq_num", in: ["num", "num"], out: "bool", fn: (a, b) => a === b },
  { name: "arr_len", in: ["arr"], out: "num", fn: (a) => a.length },
  { name: "arr_sum", in: ["arr"], out: "num", fn: (a) => a.reduce((x, y) => x + y, 0) },
  { name: "arr_max", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.max(...a) : 0) },
  { name: "arr_min", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.min(...a) : 0) },
  { name: "arr_reverse", in: ["arr"], out: "arr", fn: (a) => [...a].reverse() },
  { name: "arr_sort", in: ["arr"], out: "arr", fn: (a) => [...a].sort((x, y) => x - y) },
  { name: "arr_is_empty", in: ["arr"], out: "bool", fn: (a) => a.length === 0 },
  { name: "arr_join", in: ["arr"], out: "str", fn: (a) => a.join(",") },
  { name: "arr_contains", in: ["arr", "num"], out: "bool", fn: (a, n) => a.includes(n) },
  { name: "arr_push", in: ["arr", "num"], out: "arr", fn: (a, n) => [...a, n] },
  { name: "arr_index_of", in: ["arr", "num"], out: "num", fn: (a, n) => a.indexOf(n) },
  { name: "arr_concat", in: ["arr", "arr"], out: "arr", fn: (a, b) => [...a, ...b] },
  { name: "str_len", in: ["str"], out: "num", fn: (a) => a.length },
  { name: "str_upper", in: ["str"], out: "str", fn: (a) => a.toUpperCase() },
  { name: "str_lower", in: ["str"], out: "str", fn: (a) => a.toLowerCase() },
  { name: "str_reverse", in: ["str"], out: "str", fn: (a) => [...a].reverse().join("") },
  { name: "str_is_empty", in: ["str"], out: "bool", fn: (a) => a.length === 0 },
  { name: "str_word_count", in: ["str"], out: "num", fn: (a) => (a.trim() ? a.trim().split(/\s+/).length : 0) },
  { name: "str_concat", in: ["str", "str"], out: "str", fn: (a, b) => a + b },
  { name: "str_contains", in: ["str", "str"], out: "bool", fn: (a, b) => a.includes(b) },
  { name: "not", in: ["bool"], out: "bool", fn: (a) => !a },
  { name: "and", in: ["bool", "bool"], out: "bool", fn: (a, b) => a && b },
  { name: "or", in: ["bool", "bool"], out: "bool", fn: (a, b) => a || b },
  { name: "xor", in: ["bool", "bool"], out: "bool", fn: (a, b) => a !== b },
];

const SIGNATURE_POOL = [
  ["num"], ["str"], ["arr"], ["bool"],
  ["num", "num"], ["str", "str"], ["arr", "num"], ["arr", "arr"], ["num", "bool"],
];

// ---------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------
function loadState() {
  if (!fs.existsSync(SKILLS_FILE)) {
    return { skills: [], growthLog: [], ticks: 0, bucketStats: {} };
  }
  try {
    const data = JSON.parse(fs.readFileSync(SKILLS_FILE, "utf-8"));
    return {
      skills: data.skills || [],
      growthLog: data.growthLog || [],
      ticks: data.ticks || 0,
      bucketStats: data.bucketStats || {},
    };
  } catch {
    return { skills: [], growthLog: [], ticks: 0, bucketStats: {} };
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
  const touched = new Set(); // which skill names got invoked (for usage tracking)
  for (const opName of program) {
    const op = registry[opName];
    if (!op) return null;
    if (op.isSkill) touched.add(opName);
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
  stacks.__touched = touched;
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
    // args[0] is whatever was on TOP of the caller's stack (it was popped
    // first). To keep behavior identical whether this skill is called
    // directly (top-level fingerprinting) or nested inside another
    // program, the value that was on top of the caller's stack must stay
    // on top of this skill's own seed stack too. Pushing in reverse order
    // achieves that (last push = top).
    const n = skill.inputTypes.length;
    skill.inputTypes.forEach((t, i) => seed[t].push(args[n - 1 - i]));
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
    registry[s.name] = { name: s.name, in: s.inputTypes, out: s.outputType, fn: null, isSkill: true };
  }
  for (const s of skills) {
    registry[s.name].fn = makeSkillFn(s, registry);
  }
  return registry;
}

// ---------------------------------------------------------------------
// Fingerprinting
// ---------------------------------------------------------------------
function fingerprintFor(program, registry, inputTypes, outputType) {
  const seededCount = inputTypes.filter((t) => t === outputType).length;
  const outputs = [];
  let sample = null;
  const dependencies = new Set();
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
    if (result.__touched) for (const d of result.__touched) dependencies.add(d);
    const outStack = result[outputType];
    if (outStack.length <= seededCount) return null;
    const value = outStack[outStack.length - 1];
    outputs.push(value);
    if (s === 0) sample = { in: inputsUsed, out: value };
  }
  return { values: outputs, serialized: JSON.stringify(outputs), sample, dependencies: [...dependencies] };
}

// Cheap single-scenario execution, used for curiosity screening.
function cheapRun(program, registry, inputTypes, outputType) {
  const seededCount = inputTypes.filter((t) => t === outputType).length;
  const seed = { num: [], str: [], arr: [], bool: [] };
  inputTypes.forEach((t, i) => seed[t].push(scenarioValue(t, 0, i)));
  const result = execute(program, registry, seed);
  if (!result) return null;
  const outStack = result[outputType];
  if (outStack.length <= seededCount) return null;
  return outStack[outStack.length - 1];
}

function bucketKey(inputTypes, outputType) {
  return `${[...inputTypes].sort().join(",")}=>${outputType}`;
}

// ---------------------------------------------------------------------
// 1. PREDICTION-BASED CURIOSITY
// ---------------------------------------------------------------------
function cheapFeature(type, value) {
  switch (type) {
    case "num": return value;
    case "bool": return value ? 1 : 0;
    case "str": return value.length;
    case "arr": return value.length + (value.every((x) => typeof x === "number") ? value.reduce((a, b) => a + b, 0) * 0.01 : 0);
    default: return 0;
  }
}

function getBucketStats(state, key) {
  if (!state.bucketStats[key]) state.bucketStats[key] = { n: 0, mean: 0, m2: 0 };
  return state.bucketStats[key];
}

// Welford's online update
function updateStats(stats, x) {
  stats.n += 1;
  const delta = x - stats.mean;
  stats.mean += delta / stats.n;
  const delta2 = x - stats.mean;
  stats.m2 += delta * delta2;
}

function surprise(stats, x) {
  if (stats.n < 3) return 1; // not enough data yet -> treat everything as interesting
  const variance = stats.m2 / stats.n;
  const sd = Math.sqrt(variance) || 0.5;
  return Math.abs(x - stats.mean) / sd;
}

// ---------------------------------------------------------------------
// 2. SIMILARITY-AWARE NOVELTY
// ---------------------------------------------------------------------
function valueDistance(type, a, b) {
  switch (type) {
    case "num":
      return Math.abs(a - b) / (1 + Math.abs(a) + Math.abs(b));
    case "bool":
      return a === b ? 0 : 1;
    case "str": {
      if (a === b) return 0;
      const setA = new Set(a), setB = new Set(b);
      const inter = [...setA].filter((c) => setB.has(c)).length;
      const union = new Set([...setA, ...setB]).size || 1;
      const jaccard = inter / union;
      const lenDiff = Math.abs(a.length - b.length) / (1 + Math.max(a.length, b.length));
      return 0.6 * (1 - jaccard) + 0.4 * lenDiff;
    }
    case "arr": {
      const feat = (arr) => [arr.length, arr.reduce((x, y) => x + (typeof y === "number" ? y : 0), 0)];
      const [la, sa] = feat(a);
      const [lb, sb] = feat(b);
      const lenD = Math.abs(la - lb) / (1 + Math.max(la, lb));
      const sumD = Math.abs(sa - sb) / (1 + Math.abs(sa) + Math.abs(sb));
      return 0.5 * lenD + 0.5 * sumD;
    }
    default:
      return 1;
  }
}

// Average distance between two fingerprints' per-scenario values.
function fingerprintDistance(outputType, valuesA, valuesB) {
  let total = 0;
  for (let i = 0; i < valuesA.length; i++) total += valueDistance(outputType, valuesA[i], valuesB[i]);
  return total / valuesA.length;
}

function nearestDistance(skills, inputTypes, outputType, values) {
  let best = Infinity;
  for (const s of skills) {
    if (s.outputType !== outputType) continue;
    if (s.inputTypes.join(",") !== inputTypes.join(",")) continue;
    if (!s.fpValues) continue;
    const d = fingerprintDistance(outputType, values, s.fpValues);
    if (d < best) best = d;
  }
  return best;
}

// ---------------------------------------------------------------------
// Strategic target selection (unchanged idea: favor under-explored buckets)
// ---------------------------------------------------------------------
function pickTarget(skills) {
  const counts = {};
  for (const s of skills) counts[bucketKey(s.inputTypes, s.outputType)] = (counts[bucketKey(s.inputTypes, s.outputType)] || 0) + 1;
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

// ---------------------------------------------------------------------
// Explore: curiosity screening -> attention on surprising candidates
// -> fuzzy novelty check -> promote
// ---------------------------------------------------------------------
function exploreOnce(registry, state) {
  const { inputs, out } = pickTarget(state.skills);
  const maxLen = Math.min(2 + Math.floor(state.skills.length / 5), 6);
  const key = bucketKey(inputs, out);
  const stats = getBucketStats(state, key);

  let attempted = 0;
  while (attempted < MAX_ATTEMPTS_PER_TICK) {
    // --- cheap screening batch ---
    const scored = [];
    for (let i = 0; i < BATCH_SIZE && attempted < MAX_ATTEMPTS_PER_TICK; i++, attempted++) {
      const program = randomProgram(registry, maxLen);
      const cheapVal = cheapRun(program, registry, inputs, out);
      if (cheapVal === null || cheapVal === undefined) continue;
      const feat = cheapFeature(out, cheapVal);
      const s = surprise(stats, feat);
      scored.push({ program, feat, s });
    }
    if (scored.length === 0) continue;

    // update the running prediction with everything we just observed
    // (learning happens whether or not anything gets promoted)
    for (const c of scored) updateStats(stats, c.feat);

    // --- attention: only the most surprising candidates get full fingerprinting ---
    scored.sort((a, b) => b.s - a.s);
    const attend = scored.slice(0, ATTEND_PER_BATCH);

    for (const cand of attend) {
      const fp = fingerprintFor(cand.program, registry, inputs, out);
      if (!fp) continue;
      const dist = nearestDistance(state.skills, inputs, out, fp.values);
      if (dist >= SIMILARITY_THRESHOLD) {
        return { program: cand.program, inputTypes: inputs, outputType: out, fp, surprise: cand.s };
      }
      // else: behaviorally too close to something already known -> not a genuine
      // new discovery, just a variant. Skip (generalization instead of bloat).
    }
  }
  return null;
}

// ---------------------------------------------------------------------
// 3. UTILITY-BASED FORGETTING
// ---------------------------------------------------------------------
function computeDependents(skills) {
  // dependents[name] = how many OTHER skills call this skill in their program
  const dependents = {};
  for (const s of skills) dependents[s.name] = 0;
  for (const s of skills) {
    const uniqueDeps = new Set((s.dependencies || []).filter((d) => d !== s.name));
    for (const d of uniqueDeps) if (d in dependents) dependents[d] += 1;
  }
  return dependents;
}

function forgetIfNeeded(state) {
  if (state.skills.length <= MAX_SKILLS) return 0;
  let removedTotal = 0;
  while (state.skills.length > MAX_SKILLS) {
    const dependents = computeDependents(state.skills);
    // leaves = skills nothing else currently depends on
    const leaves = state.skills.filter((s) => dependents[s.name] === 0);
    if (leaves.length === 0) break; // everything is load-bearing; stop
    // utility score: fewer dependents already 0 (they're all leaves here),
    // so rank leaves by age (oldest = least recently useful) — a simple
    // recency/utility proxy, like fading unused memories.
    leaves.sort((a, b) => new Date(a.learnedAt) - new Date(b.learnedAt));
    const toRemove = leaves[0];
    state.skills = state.skills.filter((s) => s.name !== toRemove.name);
    removedTotal++;
  }
  return removedTotal;
}

// ---------------------------------------------------------------------
// Sleep / consolidation
// ---------------------------------------------------------------------
function consolidate(state) {
  const registry = buildRegistry(state.skills);
  const kept = [];
  for (const s of state.skills) {
    const fp = fingerprintFor(s.program, registry, s.inputTypes, s.outputType);
    if (!fp) continue; // no longer reproducible -> drop
    kept.push(s);
  }
  state.skills = kept;
  const forgotten = forgetIfNeeded(state);

  const byOutput = {};
  for (const s of state.skills) byOutput[s.outputType] = (byOutput[s.outputType] || 0) + 1;
  const lengths = state.skills.map((s) => s.program.length);
  const maxLen = lengths.length ? Math.max(...lengths) : 0;
  const dependents = computeDependents(state.skills);
  const mostRelied = Object.entries(dependents).sort((a, b) => b[1] - a[1])[0];

  console.log(
    `\n--- consolidation --- total: ${state.skills.length} | forgotten (over cap): ${forgotten} | ` +
      `by output type: ${JSON.stringify(byOutput)} | deepest program: ${maxLen} steps | ` +
      `most relied-on skill: ${mostRelied ? `${mostRelied[0]} (${mostRelied[1]} dependents)` : "none"}`
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
  const found = exploreOnce(registry, state);
  const time = new Date().toLocaleTimeString();

  if (found) {
    const skillName = `skill_${state.skills.length + 1}_${found.inputTypes.join("_")}_to_${found.outputType}`;
    state.skills.push({
      name: skillName,
      inputTypes: found.inputTypes,
      outputType: found.outputType,
      program: found.program,
      fpValues: found.fp.values,
      dependencies: found.fp.dependencies,
      learnedAt: new Date().toISOString(),
    });
    state.growthLog.push({ t: Date.now(), total: state.skills.length });
    if (state.growthLog.length > GROWTH_LOG_CAP) state.growthLog.shift();

    console.log(
      `[${time}] new behavior: ${skillName} (surprise=${found.surprise.toFixed(2)})\n` +
        `  program: [${found.program.join(" -> ")}]\n` +
        `  example: ${JSON.stringify(found.fp.sample.in)} -> ${JSON.stringify(found.fp.sample.out)}`
    );
    console.log(`  total skills: ${state.skills.length}\n`);
    saveState(state);
  } else if (!QUIET) {
    console.log(`[${time}] exploring... nothing surprising+novel enough this tick. total skills: ${state.skills.length}`);
  }

  state.ticks++;
  if (state.ticks % SLEEP_EVERY_N_TICKS === 0) {
    consolidate(state);
    saveState(state);
  }
}

async function runForever() {
  console.log(
    "Mind2 online. Prediction-based curiosity + similarity-aware novelty + utility-based forgetting.\n" +
      "Objective: still intrinsic novelty — but attention now follows surprise, and unused skills fade.\n"
  );
  const state = loadState();
  let n = 0;
  while (n < TICK_LIMIT) {
    await tick(state);
    n++;
    if (n < TICK_LIMIT) await new Promise((resolve) => setTimeout(resolve, TICK_MS));
  }
  saveState(state);
  console.log(`\n(stopped after ${n} ticks)`);
}

runForever();
