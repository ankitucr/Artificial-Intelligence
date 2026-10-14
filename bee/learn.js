#!/usr/bin/env node
/**
 * learn.js — simple self-learner
 * Kaam sirf ek hi hai: DuckDuckGo se ek topic search karo,
 * jo naya seekha usse apni khud ki knowledge file (self.json) mein save karo.
 *
 * Usage:
 *   node learn.js "topic yahan likho"
 *
 * Har run par ye:
 *  1. DuckDuckGo Instant Answer API se topic ka info nikalta hai
 *  2. Usse self.json mein append karta hai (apply-to-self = apni memory badhana)
 *  3. Screen par dikhata hai ki kya seekha
 */

const fs = require("fs");
const path = require("path");

const KNOWLEDGE_FILE = path.join(__dirname, "self.json");

function loadKnowledge() {
  if (!fs.existsSync(KNOWLEDGE_FILE)) return { learned: [] };
  try {
    return JSON.parse(fs.readFileSync(KNOWLEDGE_FILE, "utf-8"));
  } catch {
    return { learned: [] };
  }
}

function saveKnowledge(data) {
  fs.writeFileSync(KNOWLEDGE_FILE, JSON.stringify(data, null, 2), "utf-8");
}

async function searchDuckDuckGo(query) {
  const url = `https://api.duckduckgo.com/?q=${encodeURIComponent(
    query
  )}&format=json&no_html=1&skip_disambig=1`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`DuckDuckGo request failed: ${res.status}`);
  const data = await res.json();

  // Sabse useful text field nikalo
  let summary = data.AbstractText || data.Answer || "";

  // Agar direct summary nahi mila, related topics se try karo
  if (!summary && Array.isArray(data.RelatedTopics)) {
    const first = data.RelatedTopics.find((t) => t.Text);
    if (first) summary = first.Text;
  }

  return {
    query,
    summary: summary || "Kuch specific nahi mila is topic par.",
    source: data.AbstractURL || null,
  };
}

async function main() {
  const topic = process.argv.slice(2).join(" ").trim();

  if (!topic) {
    console.log('Usage: node learn.js "topic yahan likho"');
    process.exit(1);
  }

  console.log(`Seekh raha hoon: "${topic}" ...`);

  let result;
  try {
    result = await searchDuckDuckGo(topic);
  } catch (err) {
    console.error("Search fail ho gaya:", err.message);
    process.exit(1);
  }

  const knowledge = loadKnowledge();

  knowledge.learned.push({
    topic: result.query,
    summary: result.summary,
    source: result.source,
    learnedAt: new Date().toISOString(),
  });

  saveKnowledge(knowledge);

  console.log("\n--- Naya seekha ---");
  console.log(result.summary);
  if (result.source) console.log(`Source: ${result.source}`);
  console.log(`\nApne self.json mein save ho gaya (total entries: ${knowledge.learned.length})`);
}

main();
