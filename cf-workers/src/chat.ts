// Platform Agent - Chat with Streaming

interface ChatRequest {
  messages: { role: string; content: string }[];
  conversation_id?: string;
  stream?: boolean;
}

// Stream from OpenAI
async function* streamLLM(messages: { role: string; content: string }[], env: {
  LLM_API_KEY: string;
  LLM_PROVIDER?: string;
}): AsyncGenerator<string> {
  const url = "https://api.openai.com/v1/chat/completions";
  
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${env.LLM_API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: messages,
      stream: true,
    }),
  });

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") return;

        try {
          const chunk = JSON.parse(data);
          const content = chunk.choices?.[0]?.delta?.content;
          if (content) yield content;
        } catch {}
      }
    }
  }
}

// Chat endpoint
export async function handleChat(request: Request, env: {
  LLM_API_KEY: string;
  DB?: any;
}): Promise<Response> {
  const body: ChatRequest = await request.json();
  const { messages, stream, conversation_id } = body;

  // Get or create conversation
  let conv_id = conversation_id;
  if (!conv_id && env.DB) {
    conv_id = crypto.randomUUID();
    await env.DB.prepare(`
      INSERT INTO conv (id, title, member, resource, created_at, updated_at)
      VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
    `).bind(conv_id, "Chat", "member", "resource").run();
  }

  // Save user message
  if (env.DB && conv_id) {
    const msg_id = crypto.randomUUID();
    await env.DB.prepare(`
      INSERT INTO message (id, conversation, role, content, created_at)
      VALUES (?, ?, 'user', ?, datetime('now'))
    `).bind(msg_id, conv_id, messages[messages.length - 1].content).run();
  }

  // Stream response
  if (stream) {
    const stream = new ReadableStream({
      start(controller) {
        (async () => {
          try {
            for await (const chunk of streamLLM(messages, env)) {
              controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ content: chunk })}\n\n`));
            }
            controller.enqueue(new TextEncoder().encode("data: [DONE]\n\n"));
          } catch (e) {
            controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ error: String(e) })}\n\n`));
          }
          controller.close();
        })();
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  }

  // Non-streaming
  const url = "https://api.openai.com/v1/chat/completions";
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${env.LLM_API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: messages,
    }),
  });

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || "";

  // Save assistant message
  if (env.DB && conv_id) {
    const msg_id = crypto.randomUUID();
    await env.DB.prepare(`
      INSERT INTO message (id, conversation, role, content, created_at)
      VALUES (?, ?, 'assistant', ?, datetime('now'))
    `).bind(msg_id, conv_id, content).run();
  }

  return Response.json({ content, conversation_id: conv_id });
}