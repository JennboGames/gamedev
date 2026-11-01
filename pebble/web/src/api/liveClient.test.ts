import { afterEach, describe, expect, it, vi } from 'vitest';
import { liveClient } from './liveClient';

function respond(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('liveClient', () => {
  it('unwraps list responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(respond(200, { items: [{ id: 'p1' }] }));
    vi.stubGlobal('fetch', fetchMock);

    expect(await liveClient.listProducts()).toEqual([{ id: 'p1' }]);
    expect(fetchMock).toHaveBeenCalledWith('/api/products', expect.objectContaining({ method: 'GET' }));
  });

  it('resolves null when no color map exists', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respond(404, { error: { code: 'NOT_FOUND', message: 'none' } })));

    expect(await liveClient.getColorMap()).toBeNull();
  });

  it('surfaces the server error message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respond(502, { error: { code: 'UPSTREAM', message: 'Amazon is down' } })));

    await expect(liveClient.searchFoundations({ query: 'foundation' })).rejects.toThrow('Amazon is down');
  });

  it('reports an unreachable server', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fetch failed')));

    await expect(liveClient.listProducts()).rejects.toThrow('Could not reach the server.');
  });
});
