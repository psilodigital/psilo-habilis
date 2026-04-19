/**
 * Gmail OAuth2 connector routes.
 *
 * GET  /api/connectors/gmail?action=authorize — Redirect to Google OAuth consent
 * GET  /api/connectors/gmail?action=callback  — Exchange code for tokens, store via gateway
 * GET  /api/connectors/gmail?action=status     — Check connector status for a company
 */

import { NextRequest, NextResponse } from "next/server";

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";
const GATEWAY_URL =
  process.env.WORKER_GATEWAY_URL || "http://localhost:8080";

// Gmail read-only scope
const GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"];

function getRedirectUri(request: NextRequest): string {
  const url = new URL(request.url);
  return `${url.origin}/api/connectors/gmail?action=callback`;
}

export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action");

  if (action === "authorize") {
    return handleAuthorize(request);
  }

  if (action === "callback") {
    return handleCallback(request);
  }

  if (action === "status") {
    return handleStatus(request);
  }

  return NextResponse.json({ error: "Unknown action" }, { status: 400 });
}

/**
 * Redirect to Google OAuth consent screen.
 * Query params: companyId (required)
 */
function handleAuthorize(request: NextRequest) {
  const companyId = request.nextUrl.searchParams.get("companyId");
  if (!companyId) {
    return NextResponse.json(
      { error: "companyId is required" },
      { status: 400 }
    );
  }

  if (!GOOGLE_CLIENT_ID) {
    return NextResponse.json(
      { error: "GOOGLE_CLIENT_ID not configured" },
      { status: 500 }
    );
  }

  const redirectUri = getRedirectUri(request);
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: GMAIL_SCOPES.join(" "),
    access_type: "offline",
    prompt: "consent",
    state: companyId, // Pass companyId through OAuth state
  });

  return NextResponse.redirect(
    `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
  );
}

/**
 * Exchange authorization code for tokens and store via gateway.
 */
async function handleCallback(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state"); // companyId
  const error = request.nextUrl.searchParams.get("error");

  if (error) {
    return NextResponse.redirect(
      new URL(
        `/dashboard/connectors?error=${encodeURIComponent(error)}`,
        request.url
      )
    );
  }

  if (!code || !state) {
    return NextResponse.json(
      { error: "Missing code or state" },
      { status: 400 }
    );
  }

  // Exchange code for tokens
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri: getRedirectUri(request),
      grant_type: "authorization_code",
    }),
  });

  if (!tokenRes.ok) {
    const err = await tokenRes.text();
    return NextResponse.redirect(
      new URL(
        `/dashboard/connectors?error=${encodeURIComponent(`Token exchange failed: ${err}`)}`,
        request.url
      )
    );
  }

  const tokens = await tokenRes.json();

  // Store credentials via gateway
  const storeRes = await fetch(`${GATEWAY_URL}/v1/connectors/credentials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      companyId: state,
      connectorId: "gmail",
      scopes: ["email_read"],
      credentials: {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_type: tokens.token_type,
        expires_in: tokens.expires_in,
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
      },
    }),
  });

  if (!storeRes.ok) {
    return NextResponse.redirect(
      new URL(
        `/dashboard/connectors?error=${encodeURIComponent("Failed to store credentials")}`,
        request.url
      )
    );
  }

  return NextResponse.redirect(
    new URL("/dashboard/connectors?success=gmail", request.url)
  );
}

/**
 * Check connector status for a company.
 * Query params: companyId (required)
 */
async function handleStatus(request: NextRequest) {
  const companyId = request.nextUrl.searchParams.get("companyId");
  if (!companyId) {
    return NextResponse.json(
      { error: "companyId is required" },
      { status: 400 }
    );
  }

  const res = await fetch(`${GATEWAY_URL}/v1/connectors/${companyId}`, {
    next: { revalidate: 10 },
  });

  if (!res.ok) {
    return NextResponse.json([]);
  }

  return NextResponse.json(await res.json());
}
