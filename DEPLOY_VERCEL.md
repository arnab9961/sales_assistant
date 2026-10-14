# Deploying Sunset Kuakata RAG Chatbot to Vercel

This full-stack Next.js RAG application is pre-configured for 1-click deployment to **Vercel**.

---

## Quick Deploy (Option A: Using Vercel CLI)

1. Open your terminal in the `chatbot` folder:
   ```bash
   cd chatbot
   ```

2. Deploy directly with Vercel CLI:
   ```bash
   npx vercel
   ```

3. Follow the on-screen prompts:
   - **Set up and deploy?** `Y`
   - **Which scope?** (Select your personal or team account)
   - **Link to existing project?** `N`
   - **Project name?** `sunset-kuakata-rag`
   - **Directory?** `./`
   - **Override build settings?** `N`

4. When prompted (or in the Vercel Dashboard under **Project Settings > Environment Variables**), add your environment variables:
   - `GROQ_API_KEY`: `YOUR_GROQ_API_KEY_HERE`
   - `GROQ_MODEL`: `openai/gpt-oss-120b`
   - `DATABASE_URL`: `postgresql://postgres:[YOUR-PASSWORD]@db.ccivcmvwhjireufzuvxs.supabase.co:5432/postgres`

5. Deploy to Production:
   ```bash
   npx vercel --prod
   ```

---

## Git-based Deploy (Option B: GitHub to Vercel Dashboard)

1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: complete RAG chatbot for Sunset Kuakata hotel share sales"
   git remote add origin https://github.com/[YOUR-USERNAME]/ai-sales-operations-assistant.git
   git branch -M main
   git push -u origin main
   ```

2. Open [vercel.com/new](https://vercel.com/new).
3. Import your GitHub repository.
4. Set **Root Directory** to `chatbot`.
5. Under **Environment Variables**, add:
   - Key: `GROQ_API_KEY` | Value: `YOUR_GROQ_API_KEY_HERE`
   - Key: `GROQ_MODEL` | Value: `openai/gpt-oss-120b`
   - Key: `DATABASE_URL` | Value: `postgresql://postgres:[YOUR-PASSWORD]@db.ccivcmvwhjireufzuvxs.supabase.co:5432/postgres`
6. Click **Deploy**. Your live production URL will be ready in under 60 seconds!

---

## Application Features

- **Grounded RAG Retrieval**: Indexed over 13 verified chunks extracted from 8 official sales operations spreadsheets.
- **Ultra-Fast Streaming**: Powered by Groq Cloud (`openai/gpt-oss-120b`).
- **Verifiable Citations**: Every response cites the exact Excel file and sheet (e.g. `Discount Price.xlsx: Sheet1`, `Estimated Budget -September 26.xlsx: 30.9.26`).
- **Knowledge Explorer**: Interactive modal allowing recruiters to inspect the underlying source documents.
- **Supabase PostgreSQL Ready**: Integrated cloud connection parameters for production database sync.
