// Test-only fixture selection and request evidence. Credentials, query data and CSV never enter the log.
import { readFileSync } from 'node:fs';
import { createServer, request } from 'node:http';

const fixtureFile = process.env.OFFLINE_SCENARIO_FILE;
const valid = new Set(['h-stale-offline', 'i-base', 'h-learning-partial', 'h-zero', 'h-scope', 'empty']);

const proxy = createServer(async (incoming, outgoing) => {
  const path = new URL(incoming.url, 'http://localhost').pathname;
  const route = path.replace(/[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}/gi, ':id');
  process.stdout.write(`${incoming.method} ${route}\n`);
  let body;
  const headers = { ...incoming.headers, host: 'localhost:8035' };
  if (incoming.method === 'POST' && path === '/api/v1/demo/sessions') {
    try {
      const scenario = readFileSync(fixtureFile, 'utf8').trim();
      const chunks = [];
      for await (const chunk of incoming) chunks.push(chunk);
      const input = JSON.parse(Buffer.concat(chunks));
      if (valid.has(scenario)) input.scenario_id = scenario;
      body = JSON.stringify(input);
      headers['content-length'] = Buffer.byteLength(body);
      delete headers['transfer-encoding'];
    } catch {
      outgoing.writeHead(400).end();
      return;
    }
  }
  const forwarded = request({ host: '127.0.0.1', port: 8035, path: incoming.url, method: incoming.method, headers }, (reply) => {
    outgoing.writeHead(reply.statusCode, reply.headers);
    reply.pipe(outgoing);
  });
  forwarded.on('error', () => outgoing.writeHead(502).end());
  outgoing.on('close', () => forwarded.destroy());
  if (body === undefined) incoming.pipe(forwarded);
  else forwarded.end(body);
});

proxy.listen(8034, '127.0.0.1');
