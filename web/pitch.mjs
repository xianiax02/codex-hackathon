const MIN_HZ = 75;
const MAX_HZ = 500;
const YIN_THRESHOLD = 0.15;


export function yinPitch(frame, sampleRate, minHz = MIN_HZ, maxHz = MAX_HZ) {
  let energy = 0;
  for (const sample of frame) energy += sample * sample;
  if (Math.sqrt(energy / frame.length) < 0.01) return null;

  const minTau = Math.max(2, Math.floor(sampleRate / maxHz));
  const maxTau = Math.min(Math.ceil(sampleRate / minHz), frame.length >> 1);
  const difference = new Float64Array(maxTau + 1);

  for (let tau = 1; tau <= maxTau; tau += 1) {
    let sum = 0;
    for (let index = 0; index < frame.length - maxTau; index += 1) {
      const delta = frame[index] - frame[index + tau];
      sum += delta * delta;
    }
    difference[tau] = sum;
  }

  const normalized = new Float64Array(maxTau + 1);
  normalized[0] = 1;
  let runningSum = 0;
  for (let tau = 1; tau <= maxTau; tau += 1) {
    runningSum += difference[tau];
    normalized[tau] = runningSum === 0 ? 1 : (difference[tau] * tau) / runningSum;
  }

  let tauEstimate = null;
  for (let tau = minTau; tau < maxTau; tau += 1) {
    if (normalized[tau] < YIN_THRESHOLD) {
      while (tau + 1 <= maxTau && normalized[tau + 1] < normalized[tau]) tau += 1;
      tauEstimate = tau;
      break;
    }
  }
  if (tauEstimate === null) return null;

  const left = normalized[tauEstimate - 1];
  const center = normalized[tauEstimate];
  const right = normalized[tauEstimate + 1] ?? center;
  const denominator = 2 * (2 * center - right - left);
  const refinedTau = denominator === 0
    ? tauEstimate
    : tauEstimate + (right - left) / denominator;
  return sampleRate / refinedTau;
}


export function normalizeContour(points) {
  if (!points.length) return [];
  const pitches = points.map(({ hz }) => hz).sort((a, b) => a - b);
  const middle = Math.floor(pitches.length / 2);
  const medianHz = pitches.length % 2
    ? pitches[middle]
    : (pitches[middle - 1] + pitches[middle]) / 2;
  return points.map((point) => ({
    ...point,
    semitone: 12 * Math.log2(point.hz / medianHz),
  }));
}


export function extractPitchContour(audioBuffer) {
  const source = audioBuffer.getChannelData(0);
  const stride = Math.max(1, Math.round(audioBuffer.sampleRate / 16000));
  const sampleRate = audioBuffer.sampleRate / stride;
  const samples = new Float32Array(Math.ceil(source.length / stride));
  for (let index = 0; index < samples.length; index += 1) {
    samples[index] = source[index * stride];
  }

  const frameSize = 1024;
  const hopSize = 512;
  const points = [];
  const duration = samples.length / sampleRate;
  for (let offset = 0; offset + frameSize <= samples.length; offset += hopSize) {
    const hz = yinPitch(samples.subarray(offset, offset + frameSize), sampleRate);
    if (hz !== null) {
      points.push({ time: (offset / sampleRate) / duration, hz });
    }
  }
  return normalizeContour(points);
}
