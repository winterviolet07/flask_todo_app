import { spawn, ChildProcess } from 'child_process';
import { promisify } from 'util';
import { exec } from 'child_process';

const execAsync = promisify(exec);

export class Server {
  private process: ChildProcess | null = null;
  private port: number;

  constructor(port: number = 5000) {
    this.port = port;
  }

  async start(): Promise<void> {
    if (this.process) {
      throw new Error('Server is already running');
    }

    // Start the Flask server
    this.process = spawn('python', ['todo.py'], {
      stdio: 'pipe',
      shell: true
    });

    // Wait for server to start
    await this.waitForServer();

    // Log server output
    this.process.stdout?.on('data', (data) => {
      console.log(`Server stdout: ${data}`);
    });

    this.process.stderr?.on('data', (data) => {
      console.error(`Server stderr: ${data}`);
    });
  }

  async stop(): Promise<void> {
    if (!this.process) {
      return;
    }

    // Kill the server process
    if (process.platform === 'win32') {
      await execAsync(`taskkill /pid ${this.process.pid} /T /F`);
    } else {
      this.process.kill('SIGTERM');
    }

    this.process = null;
  }

  private async waitForServer(retries: number = 30): Promise<void> {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(`http://localhost:${this.port}/`);
        if (response.ok) {
          return;
        }
      } catch (error) {
        // Server not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error(`Server failed to start on port ${this.port}`);
  }
} 