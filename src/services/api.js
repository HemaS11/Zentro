export async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Request failed');
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function fetchJSON(url, options = {}) {
  return requestJSON(url, { method: 'GET', ...options });
}

export function postJSON(url, payload, options = {}) {
  return requestJSON(url, {
    method: 'POST',
    body: JSON.stringify(payload),
    ...options
  });
}
