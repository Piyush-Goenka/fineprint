import { NextResponse } from "next/server";
import { marketData } from "@/lib/market-data";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  const apiBase = process.env.NEXT_PUBLIC_FINEPRINT_API;
  if (apiBase) {
    try {
      const response = await fetch(`${apiBase}/models`, { cache: "no-store" });
      if (response.ok) return NextResponse.json(await response.json(), { headers: { "Cache-Control": "no-store" } });
    } catch { /* use the last checked-in catalog snapshot while the API is unavailable */ }
  }
  return NextResponse.json({ models: marketData.catalog, as_of: marketData.as_of }, { headers: { "Cache-Control": "no-store" } });
}
