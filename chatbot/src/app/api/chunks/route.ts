import { NextResponse } from "next/server";
import knowledgeChunks from "@/data/knowledge_base.json";

export async function GET() {
  return NextResponse.json({
    total_chunks: knowledgeChunks.length,
    chunks: knowledgeChunks,
  });
}
