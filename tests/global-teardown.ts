async function globalTeardown() {
  const server = (global as any).__server;
  if (server) {
    await server.stop();
  }
}

export default globalTeardown; 