import assert from "node:assert/strict";
import test from "node:test";

import { normalizeContour, yinPitch } from "../web/pitch.mjs";


function sineWave(frequency, sampleRate = 16000, length = 2048) {
  return Float32Array.from(
    { length },
    (_, index) => 0.7 * Math.sin((2 * Math.PI * frequency * index) / sampleRate),
  );
}

test("YIN detects a voiced 220Hz frame", () => {
  const detected = yinPitch(sineWave(220), 16000);
  assert.ok(Math.abs(detected - 220) < 3, `detected ${detected}`);
});

test("YIN abstains on silence", () => {
  assert.equal(yinPitch(new Float32Array(2048), 16000), null);
});

test("contour is normalized around its median pitch", () => {
  const points = normalizeContour([
    { time: 0, hz: 100 },
    { time: 0.5, hz: 200 },
    { time: 1, hz: 400 },
  ]);

  assert.deepEqual(points.map(({ semitone }) => Math.round(semitone)), [-12, 0, 12]);
});
