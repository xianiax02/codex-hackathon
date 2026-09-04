import assert from "node:assert/strict";
import test from "node:test";

import { transition } from "../web/state.mjs";


test("the rehearsal follows the approved path", () => {
  assert.equal(transition("idle", "CONTEXT_RECORDING"), "context");
  assert.equal(transition("context", "CONTEXT_READY"), "question");
  assert.equal(transition("question", "FIRST_ANALYZED"), "feedback");
  assert.equal(transition("feedback", "RETRY_STARTED"), "retry");
  assert.equal(transition("retry", "RETRY_ANALYZED"), "feedback");
  assert.equal(transition("feedback", "NEXT_QUESTION"), "question");
  assert.equal(transition("feedback", "COMPLETE"), "complete");
});

test("a user may continue without retrying", () => {
  assert.equal(transition("feedback", "NEXT_QUESTION"), "question");
});

test("an invalid transition is rejected", () => {
  assert.throws(
    () => transition("idle", "RETRY_ANALYZED"),
    /허용되지 않은 화면 전환/,
  );
});
