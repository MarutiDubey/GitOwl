# GitOwl Dashboard

This is the Next.js frontend for GitOwl. It provides a clean, visual interface to manage your connected repositories, view usage analytics (like tokens and cost), and set review policies.

## Setup Locally

Make sure you have Node.js installed, then run:

```bash
npm install
npm run dev
//test commit
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

## Tech Stack
- Next.js 14 (App Router)
- Tailwind CSS v4
- Prisma (SQLite for local dev)
- NextAuth.js for GitHub login
- Framer Motion for UI animations

## Database
We use SQLite for local development. To reset or apply changes to the schema, just run:
```bash
npx prisma generate
npx prisma db push
```
