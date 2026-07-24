// Stable anonymous user id, persisted so a visitor keeps the same variant.
export function getUserId() {
  let id = localStorage.getItem('copilot_uid');
  if (!id) {
    id = `u_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem('copilot_uid', id);
  }
  return id;
}
