import { Server } from './server';

async function globalSetup() {
  const server = new Server(5000);
  await server.start();
  
  // Store server reference for teardown
  (global as any).__server = server;
}

export default globalSetup; 