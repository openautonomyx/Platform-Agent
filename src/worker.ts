/**
 * Platform Agent - Cloudflare Worker
 * 
 * SurrealDB + Ollama in one worker
 */

export interface Env {
  SURREALDB_URL: string;
  SURREALDB_USER: string;
  SURREALDB_PASS: string;
  OLLAMA_URL: string;
}

const DEFAULT_SYSTEM = `You are Platform Agent, an AI assistant with persistent memory.`;

// ============================================================================
// SurrealDB Client (minimal)
// ============================================================================

class SurrealDB {
  constructor(
    private url: string,
    private user: string,
    private pass: string,
  ) {}

  async signin() {
    const res = await this.fetch("/signin", {
      method: "POST",
      body: JSON.stringify({ username: this.user, password: this.pass }),
    });
    return res.token;
  }

  async use(ns: string, db: string) {
    await this.fetch("/", { method: "POST", body: JSON.stringify({ ns, db }) });
  }

  async query(sql: string) {
    const res = await this.fetch("/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    });
    return res;
  }

  async create(table: string, data: any) {
    const res = await this.fetch(`/create/${table}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res;
  }

  private token = "";
  private ns = "";
  private db = "";

  private async fetch(path: string, init: RequestInit = {}) {
    const url = `${this.url}${path}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    };
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;

    const res = await fetch(url, { ...init, headers });
    return await res.json();
  }
}

// ============================================================================
// Ollama Client
// ============================================================================

class Ollama {
  constructor(private url: string) {}

  async chat(model: string, messages: { role: string; content: string }[]) {
    const res = await fetch(`${this.url}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages }),
    });
    const data = await res.json();
    return data.message.content;
  }
}

// ============================================================================
// Platform Agent Worker
// ============================================================================

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);

    // CORS
    if (req.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // Routes
    if (url.pathname === "/api/chat") {
      return handleChat(req, env);
    }
    if (url.pathname === "/api/memory") {
      return handleMemory(req, env);
    }
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};

async function handleChat(req: Request, env: Env): Promise<Response> {
  const db = new SurrealDB(
    env.SURREALDB_URL || "https://demo龙头.com/rpc",
    env.SURREALDB_USER || "root",
    env.SURREALDB_PASS || "root",
  );

  const ollama = new Ollama(env.OLLAMA_URL || "http://localhost:11434");

  try {
    // Sign in to SurrealDB
    const token = await db.signin();
    db.token = token;
    await db.use("platform", "agent");

    // Get conversation
    const history = await db.query(
      "SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 10",
    );

    // Build messages
    const messages = [
      { role: "system" as const, content: DEFAULT_SYSTEM },
    ];

    // Add history (reversed)
    if (history && Array.isArray(history)) {
      for (const msg of history.reverse()) {
        messages.push({ role: "user", content: msg.query || "" });
        messages.push({ role: "assistant", content: msg.response || "" });
      }
    }

    // Add current message
    const { message } = await req.json();
    messages.push({ role: "user", content: message });

    // Generate response
    const response = await ollama.chat("tinyllama", messages);

    // Store conversation
    await db.create("conversations", {
      query: message,
      response: response,
      timestamp: "time::now()",
    });

    return new Response(JSON.stringify({ response }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err.message || "Failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
}

async function handleMemory(req: Request, env: Env): Promise<Response> {
  const db = new SurrealDB(
    env.SURREALDB_URL,
    env.SURREALDB_USER,
    env.SURREALDB_PASS,
  );

  const { action, content, type } = await req.json();

  try {
    const token = await db.signin();
    db.token = token;
    await db.use("platform", "agent");

    if (action === "get") {
      const memories = await db.query(
        `SELECT * FROM memories ORDER BY timestamp DESC LIMIT 20`,
      );
      return new Response(JSON.stringify({ memories }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (action === "add") {
      const result = await db.create("memories", {
        content,
        type: type || "general",
        timestamp: "time::now()",
      });
      return new Response(JSON.stringify({ ok: true, memory: result }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ error: "Invalid action" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}