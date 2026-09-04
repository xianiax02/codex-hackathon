import { transition } from "./state.mjs";
import { extractPitchContour } from "./pitch.mjs";

let state = "idle";
let recorder = null;
let stream = null;
let chunks = [];
let firstAudioUrl = null;
let firstResult = null;
let maxTurns = 3;
let currentTurn = 1;
let turnPlan = [];
let tomorrowCard = null;
let firstContour = [];
const collectedTargets = [];

const $ = (selector) => document.querySelector(selector);
const views = ["idle", "question", "feedback", "retry", "complete"];

function setState(next) {
  state = next;
  document.body.dataset.state = next;
  const visibleState = next === "context" ? "idle" : next;
  views.forEach((name) => {
    $(`#${name}-view`).classList.toggle("active", name === visibleState);
  });

  const progress = next === "idle" || next === "context"
    ? "mission"
    : next === "question" || next === "feedback"
      ? "practice"
      : "review";
  document.querySelectorAll("[data-progress]").forEach((item) => {
    item.classList.toggle("active", item.dataset.progress === progress);
  });
}

function move(event) {
  setState(transition(state, event));
}

function setStatus(text) {
  $("#call-status-text").textContent = text;
}

function renderTurn() {
  const plan = turnPlan[currentTurn - 1];
  if (plan) {
    $("#teacher-question").textContent = plan.teacher_question_ko;
    $("#feedback-question").textContent = plan.teacher_question_ko;
  }
  $("#turn-counter").textContent = `对话 ${currentTurn}/${maxTurns}`;
  $("#retry-button").hidden = false;
  $("#pitch-card").hidden = true;
  $("#next-button").textContent = currentTurn < maxTurns ? "下一段对话" : "完成练习";
}

async function pitchFromBlob(blob) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return [];
  const context = new AudioContextClass();
  try {
    const buffer = await context.decodeAudioData(await blob.arrayBuffer());
    return extractPitchContour(buffer);
  } catch {
    return [];
  } finally {
    await context.close();
  }
}

function contourPoints(contour) {
  return contour.map(({ time, semitone }) => {
    const x = 12 + Math.max(0, Math.min(1, time)) * 576;
    const y = 75 - Math.max(-8, Math.min(8, semitone)) * 7.5;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function pitchRange(contour) {
  const values = contour.map(({ semitone }) => semitone);
  return values.length ? Math.max(...values) - Math.min(...values) : 0;
}

function renderPitchComparison(retryContour) {
  const card = $("#pitch-card");
  card.hidden = false;
  if (firstContour.length < 4 || retryContour.length < 4) {
    $("#first-contour").setAttribute("points", "");
    $("#retry-contour").setAttribute("points", "");
    $("#pitch-summary").textContent = "声音太短，无法比较音高变化。请再录一次。";
    return;
  }
  $("#first-contour").setAttribute("points", contourPoints(firstContour));
  $("#retry-contour").setAttribute("points", contourPoints(retryContour));
  $("#pitch-summary").textContent = `第一次 ${firstContour.length} 个有效区间、音高范围 ${pitchRange(firstContour).toFixed(1)} 半音；再试一次 ${retryContour.length} 个有效区间、${pitchRange(retryContour).toFixed(1)} 半音。`;
}

function showError(message) {
  $("#error-message").textContent = message;
}

function renderAnalysisMode(mode) {
  $("#analysis-notice").textContent = mode === "live"
    ? "LIVE：语音转写、语言反馈和重试分数根据本次录音生成。"
    : "FIXTURE：语音转写或 AI 调用不可用，正在使用固定验证数据。";
}

async function postAudio(path, blob) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": blob.type || "audio/webm" },
    body: blob,
  });
  if (!response.ok) {
    throw new Error(`请求失败 (${response.status})`);
  }
  return response.json();
}

function stopTracks() {
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
}

async function toggleRecording(button, onComplete) {
  showError("");
  if (recorder?.state === "recording") {
    recorder.stop();
    button.classList.remove("recording");
    button.querySelector(".button-copy").textContent = "分析中…";
    button.disabled = true;
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    showError("此浏览器无法使用麦克风。请使用最新版 Chrome。 ");
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    });
    recorder.addEventListener("stop", async () => {
      const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
      stopTracks();
      try {
        await onComplete(blob);
      } catch (error) {
        showError(`没有生成分析结果。请再录一次。${error.message}`);
        button.disabled = false;
      }
    }, { once: true });
    recorder.start();
    button.classList.add("recording");
    button.querySelector(".button-copy").textContent = "录音中 · 结束";
    setStatus("录音中");
  } catch {
    stopTracks();
    showError("无法打开麦克风。请允许麦克风权限后重试。 ");
  }
}

function renderContext(context) {
  renderAnalysisMode(context.analysis_mode);
  maxTurns = context.max_turns || 3;
  turnPlan = context.turn_plan || [];
  $("#mission-title").textContent = context.mission;
  $("#mission-detail").textContent = context.mission_detail;
  $("#source-transcript").textContent = context.source_transcript;
  $("#counterpart").textContent = context.counterpart;
  $("#purpose").textContent = context.purpose;
  $("#channel").textContent = context.channel;
  $("#teacher-question").textContent = context.teacher_question;
  $("#feedback-question").textContent = context.teacher_question;
  $("#required-list").replaceChildren(
    ...context.required_information.map((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      return li;
    }),
  );
  renderTurn();
}

function renderFeedback(result, audioBlob, contour) {
  renderAnalysisMode(result.analysis_mode);
  firstResult = result;
  firstContour = contour;
  const language = result.feedback.language;
  const pronunciation = result.feedback.pronunciation;
  $("#first-transcript").textContent = result.transcript;
  $("#language-priority").textContent = language.priority;
  $("#language-target").textContent = language.target;
  $("#language-explanation").textContent = language.explanation;
  $("#first-score").textContent = pronunciation.score;
  $("#first-score-bar").style.width = `${pronunciation.score}%`;
  $("#pronunciation-status").textContent = pronunciation.status;
  $("#focus-word").textContent = pronunciation.focus_word;
  $("#pronunciation-guide").textContent = pronunciation.guide;
  $("#retry-target").textContent = result.target_sentence;
  collectedTargets[currentTurn - 1] = result.target_sentence;

  if (firstAudioUrl) URL.revokeObjectURL(firstAudioUrl);
  firstAudioUrl = URL.createObjectURL(audioBlob);
  $("#first-audio").src = firstAudioUrl;
}

function renderRetryFeedback(result, retryContour) {
  renderAnalysisMode(result.analysis_mode);
  tomorrowCard = result.tomorrow_card || tomorrowCard;
  const pronunciation = result.feedback.pronunciation;
  $("#first-score").textContent = `${result.comparison.before} → ${result.comparison.after}`;
  $("#first-score-bar").style.width = `${pronunciation.score}%`;
  $("#pronunciation-status").textContent = pronunciation.status;
  $("#pronunciation-guide").textContent = pronunciation.guide;
  $("#retry-button").hidden = true;
  $("#next-button").textContent = currentTurn < maxTurns ? "下一段对话" : "完成练习";
  renderPitchComparison(retryContour);
}

function fallbackCard() {
  return {
    sentences: [
      collectedTargets[0] || "선생님, 민수가 아파서 내일 학교에 가지 못합니다.",
      collectedTargets[1] || "민수가 열이 조금 나요.",
      collectedTargets[2] || "내일 상태를 보고 다시 연락드리겠습니다.",
    ],
    expected_question: "병원에는 다녀왔나요?",
  };
}

function renderComplete(result = {}) {
  const card = result.tomorrow_card || tomorrowCard || fallbackCard();
  $("#tomorrow-sentences").replaceChildren(
    ...card.sentences.map((sentence) => {
      const li = document.createElement("li");
      li.textContent = sentence;
      return li;
    }),
  );
  $("#expected-question").textContent = card.expected_question;
  const comparison = $("#comparison");
  comparison.hidden = !result.comparison;
  if (result.comparison) {
    $("#before-score").textContent = `${result.comparison.before}分`;
    $("#after-score").textContent = `${result.comparison.after}分`;
  }
  setStatus("练习完成");
}

$("#context-record").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  if (state === "idle") move("CONTEXT_RECORDING");
  await toggleRecording(button, async (blob) => {
    const context = await postAudio("/api/context", blob);
    renderContext(context);
    button.disabled = false;
    button.querySelector(".button-copy").textContent = "开始说话";
    move("CONTEXT_READY");
    setStatus("通话中");
  });
});

$("#answer-record").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  await toggleRecording(button, async (blob) => {
    const parameters = new URLSearchParams({
      attempt: "first",
      turn: String(currentTurn),
      teacher_question: turnPlan[currentTurn - 1]?.teacher_question_ko || "",
    });
    const [result, contour] = await Promise.all([
      postAudio(`/api/attempts?${parameters}`, blob),
      pitchFromBlob(blob),
    ]);
    renderFeedback(result, blob, contour);
    button.disabled = false;
    button.querySelector(".button-copy").textContent = "用韩语回答";
    move("FIRST_ANALYZED");
    setStatus("即时反馈");
  });
});

$("#retry-button").addEventListener("click", () => {
  move("RETRY_STARTED");
  setStatus("再说一次");
});

$("#retry-record").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  await toggleRecording(button, async (blob) => {
    const parameters = new URLSearchParams({
      attempt: "retry",
      turn: String(currentTurn),
      teacher_question: turnPlan[currentTurn - 1]?.teacher_question_ko || "",
      target_sentence: collectedTargets[currentTurn - 1] || "",
      previous_score: String(firstResult?.feedback.pronunciation.score ?? ""),
    });
    const [result, contour] = await Promise.all([
      postAudio(`/api/attempts?${parameters}`, blob),
      pitchFromBlob(blob),
    ]);
    renderRetryFeedback(result, contour);
    button.disabled = false;
    button.querySelector(".button-copy").textContent = "再说一次";
    move("RETRY_ANALYZED");
  });
});

$("#next-button").addEventListener("click", () => {
  if (currentTurn < maxTurns) {
    currentTurn += 1;
    renderTurn();
    move("NEXT_QUESTION");
    setStatus("通话中");
    return;
  }
  renderComplete();
  move("COMPLETE");
});

$("#reset-button").addEventListener("click", () => window.location.reload());
