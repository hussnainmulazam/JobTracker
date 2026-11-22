import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { backendFetch, API_BASE_URL } from "@/lib/api";

export async function GET(request: Request) {
  try {
    const cookieStore = await cookies();
    const cookieToken = cookieStore.get("auth_token")?.value;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace(/^Bearer\s+/i, "") || cookieToken;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let response: Response | null = null;
    let fetchError: any = null;

    // Try primary API_BASE_URL
    try {
      response = await backendFetch("/api/v1/auth/google/login", {
        method: "GET",
        headers,
        cache: "no-store",
      });
    } catch (err: any) {
      fetchError = err;
      // If localhost failed (common IPv6 ::1 vs 127.0.0.1 issue in Node.js), try 127.0.0.1
      if (API_BASE_URL.includes("localhost")) {
        const fallbackUrl = API_BASE_URL.replace("localhost", "127.0.0.1");
        try {
          response = await backendFetch(`${fallbackUrl}/api/v1/auth/google/login`, {
            method: "GET",
            headers,
            cache: "no-store",
          });
          fetchError = null;
        } catch (fallbackErr: any) {
          fetchError = fallbackErr;
        }
      }
    }

    if (!response) {
      return NextResponse.json(
        { detail: `FastAPI backend server is unreachable. Please ensure it is running on ${API_BASE_URL}.` },
        { status: 503 }
      );
    }

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to retrieve Google Workspace Auth URL" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { detail: error?.message || "Failed to connect to backend server" },
      { status: 500 }
    );
  }
}
