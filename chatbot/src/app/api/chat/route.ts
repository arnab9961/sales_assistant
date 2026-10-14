import { NextRequest, NextResponse } from "next/server";
import { retrieveRelevantChunks, formatRAGPrompt } from "@/lib/rag";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { messages, apiKey: clientApiKey, model = "openai/gpt-oss-120b", temperature = 0.2 } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: "Invalid request: messages array is required." },
        { status: 400 }
      );
    }

    // Determine Groq API Key (priority: client header/body > env var)
    const apiKey = clientApiKey || process.env.GROQ_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        {
          error:
            "No Groq API Key found. Please add GROQ_API_KEY to your Vercel Environment Variables or enter your Groq API key in the Chat Settings modal.",
        },
        { status: 401 }
      );
    }

    // Extract the most recent user query
    const userMessages = messages.filter((m: { role: string }) => m.role === "user");
    const lastUserQuery = userMessages.length > 0 ? userMessages[userMessages.length - 1].content : "";

    // Run RAG Retrieval
    const searchResults = retrieveRelevantChunks(lastUserQuery, 5);
    const { systemPrompt, sources } = formatRAGPrompt(lastUserQuery, searchResults);

    // Build the messages payload with the injected RAG System Prompt
    const fullMessages = [
      { role: "system", content: systemPrompt },
      ...messages.slice(-8), // include recent conversation context
    ];

    // Call Groq API via Streaming
    const groqResponse = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: model || "llama-3.3-70b-versatile",
        messages: fullMessages,
        temperature: Math.max(0, Math.min(1, temperature)),
        stream: true,
      }),
    });

    if (!groqResponse.ok) {
      const errorText = await groqResponse.text();
      let errorJson;
      try {
        errorJson = JSON.parse(errorText);
      } catch {
        // fallback
      }
      const message = errorJson?.error?.message || errorText || "Groq API error";
      return NextResponse.json({ error: `Groq API Error: ${message}` }, { status: groqResponse.status });
    }

    if (!groqResponse.body) {
      return NextResponse.json({ error: "No response stream from Groq." }, { status: 500 });
    }

    // Create an SSE ReadableStream that first emits the retrieved sources, then tokens
    const reader = groqResponse.body.getReader();
    const decoder = new TextDecoder();
    const encoder = new TextEncoder();

    const stream = new ReadableStream({
      async start(controller) {
        // First, emit the retrieved sources metadata event
        const sourcesEvent = `data: ${JSON.stringify({ sources })}\n\n`;
        controller.enqueue(encoder.encode(sourcesEvent));

        let buffer = "";

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed || trimmed.startsWith(":")) continue;

              if (trimmed === "data: [DONE]") {
                controller.enqueue(encoder.encode("data: [DONE]\n\n"));
                continue;
              }

              if (trimmed.startsWith("data: ")) {
                try {
                  const parsed = JSON.parse(trimmed.slice(6));
                  const text = parsed.choices?.[0]?.delta?.content || "";
                  if (text) {
                    controller.enqueue(
                      encoder.encode(`data: ${JSON.stringify({ text })}\n\n`)
                    );
                  }
                } catch {
                  // pass on unparseable chunk
                }
              }
            }
          }
        } catch (streamErr) {
          controller.error(streamErr);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: errorMsg }, { status: 500 });
  }
}
