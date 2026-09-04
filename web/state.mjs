const transitions = {
  idle: { CONTEXT_RECORDING: "context" },
  context: { CONTEXT_READY: "question", RESET: "idle" },
  question: { FIRST_ANALYZED: "feedback", RESET: "idle" },
  feedback: {
    RETRY_STARTED: "retry",
    NEXT_QUESTION: "question",
    COMPLETE: "complete",
    RESET: "idle",
  },
  retry: { RETRY_ANALYZED: "feedback", RESET: "idle" },
  complete: { RESET: "idle" },
};


export function transition(state, event) {
  const next = transitions[state]?.[event];
  if (!next) {
    throw new Error(`허용되지 않은 화면 전환: ${state} + ${event}`);
  }
  return next;
}
