#!/usr/bin/env node
/**
 * mind.js — chhota sa self-directed dimag
 *
 * Pehle version mein maine khud "challenges" aur "sahi jawab" (reference
 * answers) likhe the — matlab mujhe pata tha kya seekhna hai, dimag sirf
 * uska raasta dhoondh raha tha. Ye asal mein seekhna nahi tha.
 *
 * Is version mein koi target nahi, koi reference answer nahi. Iska sirf
 * ek hi motive hai: "kuch aisa karo jo pehle kabhi nahi kiya" — yani
 * naya, distinct behavior discover karna (novelty-driven exploration,
 * bilkul jaise baby random haath-pair hilata hai aur notice karta hai
 * jab kuch naya hota hai).
 *
 * Kaise kaam karta hai:
 *  1. Apne paas jo bhi reflexes (primitives) + pehle seekhi skills hain,
 *     unko RANDOM order mein combine karta hai
 *  2. Us combination ko kuch FIXED "standard stimuli" (test inputs) par
 *     chalata hai — jaise baby ke saamne hamesha wahi khilone rakhe hon
 *  3. Jo result milta hai, use apni "memory of known behaviors" se compare
 *     karta hai
 *  4. Agar ye result KABHI NAHI DEKHA — naya hai — toh isse permanent
 *     skill bana ke rakh leta hai
 *  5. Agar pehle se dekha hua hai (chahe kisi bhi purane program se aaya
 *     ho), discard kar deta hai — koi fayda nahi dobara wahi seekhne mein
 *
 * Purani skills khud future combinations ke liye building-blocks ban
 * jaati hain — isliye seekhna cumulative aur deeper hota jaata hai.
 *
 * Chalane ke liye:
 *   node mind.js
 */

const fs = require("fs");
const path = require("path");

const SKILLS_FILE = path.join(__dirname, "skills.json");
const TICK_MS = 4000;
const ATTEMPTS_PER_TICK = 6000;

// ---------- Reflexes (primitives) ----------
// Ye jaise baby ke paidaishi reflexes hain — inhe khud seekha nahi jaata,
// inhi ke through duniya ko "chua" (interact) jaata hai.
const BASE_PRIMITIVES = [
  { name: "add", in: ["num", "num"], out: "num", fn: (a, b) => a + b },
  { name: "sub", in: ["num", "num"], out: "num", fn: (a, b) => a - b },
  { name: "mul", in: ["num", "num"], out: "num", fn: (a, b) => a * b },
  { name: "inc", in: ["num"], out: "num", fn: (a) => a + 1 },
  { name: "dec", in: ["num"], out: "num", fn: (a) => a - 1 },
  { name: "neg", in: ["num"], out: "num", fn: (a) => -a },
  { name: "abs", in: ["num"], out: "num", fn: (a) => Math.abs(a) },
  { name: "is_even", in: ["num"], out: "bool", fn: (a) => a % 2 === 0 },
  { name: "is_odd", in: ["num"], out: "bool", fn: (a) => a % 2 !== 0 },
  { name: "is_positive", in: ["num"], out: "bool", fn: (a) => a > 0 },

  { name: "arr_len", in: ["arr"], out: "num", fn: (a) => a.length },
  { name: "arr_sum", in: ["arr"], out: "num", fn: (a) => a.reduce((x, y) => x + y, 0) },
  { name: "arr_max", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.max(...a) : 0) },
  { name: "arr_min", in: ["arr"], out: "num", fn: (a) => (a.length ? Math.min(...a) : 0) },
  { name: "arr_reverse", in: ["arr"], out: "arr", fn: (a) => [...a].reverse() },
  { name: "arr_sort", in: ["arr"], out: "arr", fn: (a) => [...a].sort((x, y) => x - y) },
  { name: "arr_is_empty", in: ["arr"], out: "bool", fn: (a) => a.length === 0 },

  { name: "str_len", in: ["str"], out: "num", fn: (a) => a.length },
  { name: "str_upper", in: ["str"], out: "str", fn: (a) => a.toUpperCase() },
  { name: "str_lower", in: ["str"], out: "str", fn: (a) => a.toLowerCase() },
  { name: "str_reverse", in: ["str"], out: "str", fn: (a) => [...a].reverse().join("") },
  { name: "str_is_empty", in: ["str"], out: "bool", fn: (a) => a.length === 0 },

  { name: "not", in: ["bool"], out: "bool", fn: (a) => !a },
];

// ---------- Standard stimuli ----------
// Ye "sahi jawab" nahi hain — sirf fixed test-cheezein jo dimag ke
// saamne baar-baar rakhi jaati hain, taaki wo apne behavior ko khud
// compare kar sake. Jaise baby ke paas roz wahi khilone hote hain.
const STIMULI = {
  num: [0, 1, -4, 8, -1],
  arr: [[], [3, 1, 2], [-5, 10, 0, 7], [9]],
  str: ["", "ab", "namaste", "duniya"],
};
const TYPES = Object.keys(STIMULI);

// ---------- Persistence ----------
function loadSkills() {
  if (!fs.existsSync(SKILLS_FILE)) return { skills: [], knownFingerprints: [] };
  try {
    const data = JSON.parse(fs.readFileSync(SKILLS_FILE, "utf-8"));
    if (!data.knownFingerprints) data.knownFingerprints = data.skills.map((s) => s.fingerprint);
    return data;
  } catch {
    return { skills: [], knownFingerprints: [] };
  }
}
function saveSkills(data) {
  fs.writeFileSync(SKILLS_FILE, JSON.stringify(data, null, 2), "utf-8");
}

// ---------- Program execution ----------
function runProgram(program, registry, inputValue, inputType) {
  let value = inputValue;
  let type = inputType;
  for (const opName of program) {
    const op = registry[opName];
    if (!op) return undefined;
    if (op.in.length !== 1 || op.in[0] !== type) return undefined;
    try {
      value = op.fn(value);
    } catch {
      return undefined;
    }
    type = op.out;
  }
  return { value, type };
}

function randomProgram(registry, maxLen) {
  const names = Object.keys(registry);
  const len = 1 + Math.floor(Math.random() * maxLen);
  const prog = [];
  for (let i = 0; i < len; i++) {
    prog.push(names[Math.floor(Math.random() * names.length)]);
  }
  return prog;
}

function buildRegistry(baseSkills, learnedSkills) {
  const registry = {};
  for (const p of baseSkills) registry[p.name] = p;
  for (const s of learnedSkills) {
    registry[s.name] = {
      name: s.name,
      in: [s.inType],
      out: s.outType,
      fn: (val) => {
        const result = runProgram(s.program, registry, val, s.inType);
        return result ? result.value : undefined;
      },
    };
  }
  return registry;
}

// Ek program ka "behavior fingerprint" — fixed stimuli par kya deta hai
function fingerprintOf(program, registry, inType) {
  const inputs = STIMULI[inType];
  const outputs = [];
  let outType = null;
  for (const inp of inputs) {
    const result = runProgram(program, registry, inp, inType);
    if (!result) return null; // invalid combination — is stimulus par kaam nahi karta
    if (outType && result.type !== outType) return null; // consistent type nahi
    outType = result.type;
    outputs.push(result.value);
  }
  return { key: `${inType}=>${outType}::${JSON.stringify(outputs)}`, outType, sample: { in: inputs[0], out: outputs[0] } };
}

function exploreOnce(registry, knownFingerprints, maxLen) {
  const inType = TYPES[Math.floor(Math.random() * TYPES.length)];

  for (let attempt = 0; attempt < ATTEMPTS_PER_TICK; attempt++) {
    const program = randomProgram(registry, maxLen);
    const fp = fingerprintOf(program, registry, inType);
    if (!fp) continue; // ye combination is type par chalta hi nahi

    if (!knownFingerprints.has(fp.key)) {
      return { program, inType, outType: fp.outType, fingerprint: fp.key, sample: fp.sample };
    }
  }
  return null;
}

// ---------- Main loop ----------
let skillCounter = 0;

async function tick() {
  const data = loadSkills();
  const registry = buildRegistry(BASE_PRIMITIVES, data.skills);
  const knownFingerprints = new Set(data.knownFingerprints);
  skillCounter = data.skills.length;

  const maxLen = Math.min(2 + Math.floor(data.skills.length / 4), 5);

  const found = exploreOnce(registry, knownFingerprints, maxLen);
  const time = new Date().toLocaleTimeString();

  if (found) {
    skillCounter++;
    const skillName = `skill_${skillCounter}_${found.inType}_to_${found.outType}`;
    data.skills.push({
      name: skillName,
      program: found.program,
      inType: found.inType,
      outType: found.outType,
      fingerprint: found.fingerprint,
      learnedAt: new Date().toISOString(),
    });
    data.knownFingerprints.push(found.fingerprint);
    saveSkills(data);

    const sampleIn = JSON.stringify(found.sample.in);
    const sampleOut = JSON.stringify(found.sample.out);
    console.log(
      `[${time}] NAYA BEHAVIOR DISCOVER KIYA: ${skillName}\n  program: [${found.program.join(" -> ")}]\n  example: ${sampleIn}  ->  ${sampleOut}`
    );
    console.log(`  Total skills: ${data.skills.length}\n`);
  } else {
    console.log(
      `[${time}] Explore kar raha hoon... (${ATTEMPTS_PER_TICK} tries mein kuch naya nahi mila is baar). Total skills: ${data.skills.length}`
    );
  }
}

async function runForever() {
  console.log(
    "Dimag jaag gaya. Koi target nahi diya gaya hai — ye khud tay karega ki kya naya try karna hai.\n" +
      "Sirf ek hi motive: jo pehle nahi kiya, wo karo.\n"
  );
  while (true) {
    await tick();
    await new Promise((resolve) => setTimeout(resolve, TICK_MS));
  }
}

runForever();
