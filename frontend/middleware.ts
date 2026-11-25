import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("auth_token")?.value;
  const { pathname } = request.nextUrl;

  // Canonical 6-Page consolidation redirects
  if (pathname === "/applications" || pathname === "/cv" || pathname === "/compare") {
    return NextResponse.redirect(new URL("/pipeline", request.url));
  }
  if (
    pathname === "/ai-tools" ||
    pathname === "/screening" ||
    pathname === "/outreach" ||
    pathname === "/agent"
  ) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  if (pathname === "/availability") {
    return NextResponse.redirect(new URL("/interviews", request.url));
  }

  const isAuthPage =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  const isProtectedPage =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/pipeline") ||
    pathname.startsWith("/inbox") ||
    pathname.startsWith("/interviews") ||
    pathname.startsWith("/openings") ||
    pathname.startsWith("/settings");

  // 1. Protect application routes: redirect unauthenticated users to /login
  if (isProtectedPage && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 2. Prevent already authenticated users from accessing /login and /register
  // If there is a 'redirect' parameter, the user was sent here due to 401/expired session — clear cookie and render login
  if (isAuthPage && token) {
    if (request.nextUrl.searchParams.has("redirect")) {
      const response = NextResponse.next();
      response.cookies.delete("auth_token");
      return response;
    }
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // 3. Redirect root / to /dashboard if logged in
  if (pathname === "/" && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/pipeline/:path*",
    "/inbox/:path*",
    "/interviews/:path*",
    "/openings/:path*",
    "/candidates/:path*",
    "/screening/:path*",
    "/compare/:path*",
    "/applications/:path*",
    "/ai-tools/:path*",
    "/cv/:path*",
    "/settings/:path*",
    "/login",
    "/register",
  ],
};
