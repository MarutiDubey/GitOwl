import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    // This is a temporary hack to add the column since Prisma db push is blocked locally
    // and Vercel's Query UI is read-only.
    await prisma.$executeRawUnsafe(`ALTER TABLE "Repository" ADD COLUMN IF NOT EXISTS "ignorePaths" TEXT;`);
    
    return NextResponse.json({ 
      success: true, 
      message: "Database schema successfully updated with ignorePaths column!" 
    });
  } catch (error: any) {
    console.error("Migration failed:", error);
    return NextResponse.json({ 
      success: false, 
      error: error.message || "Failed to update database schema." 
    }, { status: 500 });
  }
}
