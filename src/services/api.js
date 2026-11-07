const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

function resolveUrl(url) {
  if (!url) {
    return url;
  }

  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/')) {
    return url;
  }

  return `${API_BASE_URL}${url}`;
}

export async function requestJSON(url, options = {}) {
  const resolvedUrl = resolveUrl(url);

  try {
    const response = await fetch(resolvedUrl, {
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const errorText = await response.text();
      let message = 'Request failed';
      try {
        const parsed = JSON.parse(errorText);
        message = parsed.detail || parsed.message || parsed.error || message;
      } catch {
        if (errorText) {
          message = errorText;
        }
      }
      throw new Error(message);
    }

    if (response.status === 204) {
      return null;
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Unable to reach the Zentro backend. Check that the API server is running on port 8000.');
    }

    throw error;
  }
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
