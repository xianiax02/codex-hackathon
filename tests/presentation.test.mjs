import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";


const htmlUrl = new URL("../presentation/index.html", import.meta.url);
const scriptUrl = new URL("../presentation/deck.js", import.meta.url);

test("the deck follows the approved six-slide timing contract", async () => {
  const html = await readFile(htmlUrl, "utf8");
  assert.equal((html.match(/class="slide(?: |")/g) || []).length, 6);
  assert.match(html, /주변 이주민 학부모/);
  assert.match(html, /두 달/);
  assert.match(html, /fixture 분석|분석 결과는 fixture/);
  assert.equal(
    [...html.matchAll(/data-seconds="(\d+)"/g)].reduce(
      (sum, match) => sum + Number(match[1]),
      0,
    ),
    150,
  );
});

test("the deck exposes navigation, timer, and configurable demo hooks", async () => {
  const html = await readFile(htmlUrl, "utf8");
  const script = await readFile(scriptUrl, "utf8");
  assert.match(html, /id="progress"/);
  assert.match(html, /id="timer"/);
  assert.match(html, /id="demo-link"/);
  assert.match(script, /ArrowRight/);
  assert.match(script, /ArrowLeft/);
  assert.match(script, /URLSearchParams/);
});
