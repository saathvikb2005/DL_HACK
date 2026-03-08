/*
  Event Router
  Maps monitoring module events → avatar speech messages.
  External modules call: window.handleEvent("EVENT_NAME")
*/

const eventMessages = {
  LOW_BLINK_RATE: "You have been staring too long. Try blinking slowly.",
  BAD_POSTURE: "Your posture looks bad. Please sit up straight.",
  HIGH_FATIGUE: "You seem tired. Consider taking a short break.",
  LONG_SESSION: "You have been working for a while. Time for a stretch.",
  POOR_AIR_QUALITY: "Air quality is poor. Consider opening a window.",
  TAKE_BREAK: "It is time for a break. Stand up and move around.",
  HYDRATE: "Remember to drink some water.",
  EYE_STRAIN: "Your eyes may be strained. Look at something 20 feet away for 20 seconds.",
  HIGH_STRESS: "Your stress levels seem elevated. Try some deep breathing.",
  EXCESSIVE_YAWNING: "You are yawning frequently. Your body needs rest. Take a break.",
};

export function getMessageForEvent(eventType) {
  return eventMessages[eventType] || null;
}

export function addCustomEvent(eventType, message) {
  eventMessages[eventType] = message;
}
