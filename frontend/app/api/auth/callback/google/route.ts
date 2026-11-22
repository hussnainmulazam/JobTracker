import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { backendFetch } from "@/lib/api";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");

  // Determine authorized redirect URI matching Google Console
  const isVercel = origin.includes("hrhiringloop.vercel.app") || process.env.NEXTAUTH_URL?.includes("hrhiringloop.vercel.app");
  const redirectUri = isVercel
    ? "https://hrhiringloop.vercel.app/api/auth/callback/google"
    : `${origin}/api/auth/callback/google`;

  // 1. Handle Google-level errors (e.g. user dismissed consent / access denied)
  if (error) {
    const errorMsg =
      error === "access_denied"
        ? "Access was denied by Google. Please approve the prompt to continue."
        : `Google sign-in error: ${error}`;

    const html = `<!DOCTYPE html>
<html>
<head><title>Google Sign-in</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({ type: "GOOGLE_AUTH_ERROR", error: ${JSON.stringify(errorMsg)} }, window.location.origin);
    window.close();
  } else {
    window.location.href = "/login?error=" + encodeURIComponent(${JSON.stringify(errorMsg)});
  }
</script>
<p>Sign-in error: ${errorMsg}. Redirecting...</p>
</body>
</html>`;
    return new NextResponse(html, {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  }

  // 2. Missing authorization code
  if (!code) {
    const errorMsg = "Missing authorization code from Google.";
    const html = `<!DOCTYPE html>
<html>
<head><title>Google Sign-in</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({ type: "GOOGLE_AUTH_ERROR", error: ${JSON.stringify(errorMsg)} }, window.location.origin);
    window.close();
  } else {
    window.location.href = "/login?error=" + encodeURIComponent(${JSON.stringify(errorMsg)});
  }
</script>
<p>${errorMsg}</p>
</body>
</html>`;
    return new NextResponse(html, {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  }

  // 3. Exchange code on backend & authenticate user
  try {
    const backendRes = await backendFetch("/api/v1/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });

    const data = await backendRes.json();
    if (!backendRes.ok) {
      const errorMsg = data.detail || "Google authentication failed on server.";
      const html = `<!DOCTYPE html>
<html>
<head><title>Google Sign-in</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({ type: "GOOGLE_AUTH_ERROR", error: ${JSON.stringify(errorMsg)} }, window.location.origin);
    window.close();
  } else {
    window.location.href = "/login?error=" + encodeURIComponent(${JSON.stringify(errorMsg)});
  }
</script>
<p>${errorMsg}</p>
</body>
</html>`;
      return new NextResponse(html, {
        status: 200,
        headers: { "Content-Type": "text/html" },
      });
    }

    // 4. Set secure HTTP-only cookie for SSR & middleware
    const isHttps = request.url.startsWith("https:") || isVercel;
    const cookieStore = await cookies();
    cookieStore.set("auth_token", data.access_token, {
      httpOnly: true,
      secure: isHttps,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    const targetDestination = data.setup_completed ? "/dashboard" : "/setup";

    // 5. Deliver token to client localStorage and redirect
    const html = `<!DOCTYPE html>
<html>
<head><title>Google Sign-in Complete</title></head>
<body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #09090b; color: #fafafa;">
<div style="text-align: center;">
  <p style="font-size: 14px; color: #a1a1aa;">Signing you in to Recruiter AI Copilot...</p>
</div>
<script>
  try {
    localStorage.setItem("job_tracker_token", ${JSON.stringify(data.access_token)});
    window.dispatchEvent(new Event("auth-change"));
  } catch (e) {}

  if (window.opener) {
    window.opener.postMessage({
      type: "GOOGLE_AUTH_SUCCESS",
      token: ${JSON.stringify(data.access_token)},
      setup_completed: ${Boolean(data.setup_completed)},
      destination: ${JSON.stringify(targetDestination)},
    }, window.location.origin);
    setTimeout(function() {
      window.close();
    }, 150);
  } else {
    window.location.href = ${JSON.stringify(targetDestination)};
  }
</script>
</body>
</html>`;

    return new NextResponse(html, {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  } catch (err: any) {
    const errorMsg = "Unable to connect to authentication server. Please check your network.";
    const html = `<!DOCTYPE html>
<html>
<head><title>Google Sign-in</title></head>
<body>
<script>
  if (window.opener) {
    window.opener.postMessage({ type: "GOOGLE_AUTH_ERROR", error: ${JSON.stringify(errorMsg)} }, window.location.origin);
    window.close();
  } else {
    window.location.href = "/login?error=" + encodeURIComponent(${JSON.stringify(errorMsg)});
  }
</script>
<p>${errorMsg}</p>
</body>
</html>`;
    return new NextResponse(html, {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  }
}
