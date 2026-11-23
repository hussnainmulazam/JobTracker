import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/api";

export async function GET(request: Request) {
  try {
    const { origin } = new URL(request.url);
    const isVercel =
      origin.includes("hrhiringloop.vercel.app") ||
      process.env.NEXTAUTH_URL?.includes("hrhiringloop.vercel.app");

    // Match exact Google Cloud Console registered redirect URIs:
    // 1. http://localhost:8000/auth/google/callback (local dev)
    // 2. https://hrhiringloop.vercel.app/api/auth/callback/google (prod Vercel)
    const redirectUri = isVercel
      ? "https://hrhiringloop.vercel.app/api/auth/callback/google"
      : "http://localhost:8000/auth/google/callback";

    const endpoint = `/api/v1/auth/google/url?redirect_uri=${encodeURIComponent(redirectUri)}`;
    const response = await backendFetch(endpoint, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to retrieve Google Auth URL" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { detail: "Failed to connect to authentication service" },
      { status: 500 }
    );
  }
}
