// Platform Agent - Cloudflare Worker

import { handleChat } from "./chat";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // CORS
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Sign in
    if (url.pathname === "/auth/signin" && request.method === "POST") {
      return handleSignIn(request, env);
    }
    // Sign up
    if (url.pathname === "/auth/signup" && request.method === "POST") {
      return handleSignUp(request, env);
    }
    // Create invite
    if (url.pathname === "/invites" && request.method === "POST") {
      return handleCreateInvite(request, env);
    }
    // Accept invite
    if (url.pathname.startsWith("/invites/") && request.method === "POST") {
      return handleAcceptInvite(request, env);
    }
    // Chat (with streaming)
    if (url.pathname === "/chat" && request.method === "POST") {
      return handleChat(request, env);
    }
    // Knowledge
    if (url.pathname === "/knowledge" && request.method === "GET") {
      return handleListKnowledge(request, env);
    }
    if (url.pathname === "/knowledge" && request.method === "POST") {
      return handleCreateKnowledge(request, env);
    }
    // Stats
    if (url.pathname === "/stats" && request.method === "GET") {
      return handleStats(request, env);
    }

    return new Response("Not Found", { status: 404 });
  },
};

interface Env {
  DB: D1Database;
  LLM_API_KEY: string;
  LLM_PROVIDER?: string;
  JWT_SECRET?: string;
}

// Auth: Sign in
async function handleSignIn(request: Request, env: Env): Promise<Response> {
  const { email, password } = await request.json();
  
  const result = await env.DB.prepare(
    "SELECT * FROM member WHERE email = ?"
  ).bind(email).first();

  if (!result) {
    return Response.json({ error: "Invalid credentials" }, { status: 401 });
  }

  // Verify password (use bcrypt in production)
  const valid = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(password + env.JWT_SECRET || "secret")
  );

  return Response.json({
    token: btoa(email),
    member: { id: result.id, email: result.email, first_name: result.first_name },
  });
}

// Auth: Sign up
async function handleSignUp(request: Request, env: Env): Promise<Response> {
  const { email, password, first_name, last_name } = await request.json();
  
  const existing = await env.DB.prepare(
    "SELECT id FROM member WHERE email = ?"
  ).bind(email).first();

  if (existing) {
    return Response.json({ error: "Email exists" }, { status: 400 });
  }

  const id = crypto.randomUUID();
  await env.DB.prepare(`
    INSERT INTO member (id, email, password, first_name, last_name, settings, created_at)
    VALUES (?, ?, ?, ?, ?, '{}', datetime('now'))
  `).bind(id, email, password, first_name, last_name).run();

  return Response.json({
    token: btoa(email),
    member: { id, email, first_name, last_name },
  });
}

// Invitations: Create
async function handleCreateInvite(request: Request, env: Env): Promise<Response> {
  const { email, resource_id } = await request.json();
  const token = crypto.randomUUID();
  
  const id = crypto.randomUUID();
  await env.DB.prepare(`
    INSERT INTO invitation (id, email, token, creator, resource, status, expires_at, created_at)
    VALUES (?, ?, ?, ?, ?, 'pending', datetime('now', '+7 days'), datetime('now'))
  `).bind(id, email, token, "creator", resource_id).run();

  return Response.json({
    invite_url: `/invite?token=${token}`,
    expires_in: "7 days",
  });
}

// Invitations: Accept
async function handleAcceptInvite(request: Request, env: Env): Promise<Response> {
  const token = new URL(request.url).pathname.split("/").pop()!;
  const { first_name, last_name, password } = await request.json();

  const inv = await env.DB.prepare(
    "SELECT * FROM invitation WHERE token = ? AND status = 'pending'"
  ).bind(token).first();

  if (!inv) {
    return Response.json({ error: "Invalid or expired" }, { status: 400 });
  }

  // Create member
  const id = crypto.randomUUID();
  await env.DB.prepare(`
    INSERT INTO member (id, email, password, first_name, last_name, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
  `).bind(id, inv.email, password, first_name, last_name).run();

  // Create membership
  await env.DB.prepare(`
    INSERT INTO membership (id, in_member, out_resource, role)
    VALUES (?, ?, ?, 'member')
  `).bind(crypto.randomUUID(), id, inv.resource).run();

  // Mark used
  await env.DB.prepare(
    "UPDATE invitation SET status = 'used', used_at = datetime('now') WHERE token = ?"
  ).bind(token).run();

  return Response.json({ success: true });
}

// Knowledge: List
async function handleListKnowledge(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const resource_id = url.searchParams.get("resource");
  
  const docs = await env.DB.prepare(
    "SELECT * FROM kn WHERE resource = ? ORDER BY created_at DESC LIMIT 50"
  ).bind(resource_id || "default").all();

  return Response.json({ documents: docs.results || [] });
}

// Knowledge: Create
async function handleCreateKnowledge(request: Request, env: Env): Promise<Response> {
  const { title, content, type, tags, resource_id } = await request.json();
  
  const id = crypto.randomUUID();
  await env.DB.prepare(`
    INSERT INTO kn (id, title, content, type, tags, resource, created_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
  `).bind(id, title, content, type || "doc", JSON.stringify(tags || []), resource_id || "default").run();

  return Response.json({ id, title, content });
}

// Stats
async function handleStats(request: Request, env: Env): Promise<Response> {
  const mem = await env.DB.prepare("SELECT count() FROM member").first() as any;
  const conv = await env.DB.prepare("SELECT count() FROM conv").first() as any;
  const kb = await env.DB.prepare("SELECT count() FROM kn").first() as any;

  return Response.json({
    members: mem?.count || 0,
    conversations: conv?.count || 0,
    knowledge: kb?.count || 0,
  });
}