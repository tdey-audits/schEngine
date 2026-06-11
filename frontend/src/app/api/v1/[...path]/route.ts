import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE = process.env.SCHENGINE_API_BASE ?? "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const url = new URL(request.url);
  const backendUrl = `${BACKEND_BASE}/api/v1/${path.join("/")}${url.search}`;
  const body = request.method === "GET" ? undefined : await request.text();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);

  try {
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: {
        "Content-Type": request.headers.get("Content-Type") ?? "application/json"
      },
      body,
      cache: "no-store",
      signal: controller.signal
    });

    const data = await response.arrayBuffer();
    const headers = new Headers();
    const contentType = response.headers.get("Content-Type");
    const disposition = response.headers.get("Content-Disposition");
    if (contentType) headers.set("Content-Type", contentType);
    if (disposition) headers.set("Content-Disposition", disposition);

    return new NextResponse(data, {
      status: response.status,
      headers
    });
  } finally {
    clearTimeout(timeout);
  }
}
