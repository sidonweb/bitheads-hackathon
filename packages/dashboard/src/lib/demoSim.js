const KEYS = {
  users: 'demo_sim_users',
  convA: 'demo_sim_conv_a',
  convB: 'demo_sim_conv_b',
  scenario: 'demo_scenario',
};

export const SCENARIOS = [
  { id: 'scale', label: 'Scale — B wins' },
  { id: 'rollback', label: 'Rollback — B loses' },
  { id: 'continue', label: 'Continue — low sample' },
  { id: 'stop', label: 'Stop — no winner' },
  { id: 'empty', label: 'Empty — just launched' },
  { id: 'live', label: 'Live — manual traffic' },
];

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

const defaults = {
  users: 500,
  convA: 15.8,
  convB: 18.0,
  scenario: 'scale',
};

function readNum(key, fallback) {
  const raw = localStorage.getItem(key);
  if (raw == null) return fallback;
  const n = Number(raw);
  return Number.isFinite(n) ? n : fallback;
}

export function readSimSettings() {
  return {
    users: readNum(KEYS.users, defaults.users),
    convA: readNum(KEYS.convA, defaults.convA),
    convB: readNum(KEYS.convB, defaults.convB),
    scenario: localStorage.getItem(KEYS.scenario) || defaults.scenario,
  };
}

export function saveSimSettings({ users, convA, convB, scenario }) {
  localStorage.setItem(KEYS.users, String(users));
  localStorage.setItem(KEYS.convA, String(convA));
  localStorage.setItem(KEYS.convB, String(convB));
  if (scenario) localStorage.setItem(KEYS.scenario, scenario);
}

export function toConvFraction(percent) {
  return Math.min(1, Math.max(0, percent / 100));
}
