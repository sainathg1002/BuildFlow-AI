"use client";

import { useState } from "react";
import axios from "axios";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "development"
    ? "http://127.0.0.1:8000"
    : "https://buildflow-ai.onrender.com")
).replace(/\/+$/, "");

type GenerateResponse = {
  app_url?: string;
  project?: string;
  error?: string;
  warning?: string;
  cached?: boolean;
  failed_files?: string[];
};

function toAbsoluteUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  const normalized = pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
  return `${API_BASE_URL}${normalized}`;
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [appUrl, setAppUrl] = useState("");
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [wasCached, setWasCached] = useState(false);

  const generateProject = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setError("");
    setWarning("");
    setAppUrl("");
    setWasCached(false);

    try {
      const response = await axios.post<GenerateResponse>(`${API_BASE_URL}/generate`, {
        prompt,
        recursion_limit: 12,
      });

      const data = response.data;
      if (data.error) {
        const failed =
          data.failed_files && data.failed_files.length
            ? ` Failed files: ${data.failed_files.join(", ")}`
            : "";
        setError(`${data.error}${failed}`);
        return;
      }

      if (!data.app_url) {
        setError("Generation completed, but no runnable app URL was returned.");
        return;
      }

      setAppUrl(toAbsoluteUrl(data.app_url));
      setWasCached(data.cached === true);
      if (data.warning) {
        setWarning(data.warning);
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const apiError = err.response?.data?.detail ?? err.response?.data?.error;
        if (apiError) {
          setError(String(apiError));
        } else if (!err.response) {
          setError(
            `Cannot reach backend API (${API_BASE_URL}). Check Render service status, CORS, and NEXT_PUBLIC_API_BASE_URL.`
          );
        } else {
          setError(`Failed to generate project (HTTP ${err.response.status}).`);
        }
      } else {
        setError("Failed to generate project.");
      }
    } finally {
      setLoading(false);
    }
  };

  const runApp = () => {
    if (!appUrl) return;
    window.open(appUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <main className="app-shell min-h-screen px-4 py-14 sm:px-8">
      <div className="relative z-10 mx-auto w-full max-w-4xl">
        <section className="fade-in-up mb-7">
          <p className="mb-4 inline-flex rounded-full border border-white/70 bg-white/70 px-4 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#0f6a78] shadow-sm backdrop-blur">
            Multi-Agent App Generator
          </p>
          <h1 className="max-w-3xl text-3xl font-normal leading-tight text-[#122034] sm:text-4xl">
            BuildFlow AI turns your idea into a working web app in minutes.
          </h1>
          <p className="mt-4 max-w-2xl text-base text-[#34475f] sm:text-lg">
            Describe what you want. The planner, architect, and coder agents generate a runnable app package you can open immediately.
          </p>
        </section>

        <section className="fade-in-up-delayed rounded-3xl border border-white/70 bg-white/75 p-5 shadow-[0_22px_60px_rgba(12,33,64,0.16)] backdrop-blur-md sm:p-8">
          <label
            htmlFor="prompt"
            className="mb-3 block text-sm font-semibold uppercase tracking-[0.16em] text-[#0f6a78]"
          >
            App Prompt
          </label>

          <textarea
            id="prompt"
            className="min-h-40 w-full rounded-2xl border border-[#d3dded] bg-[#ffffff]/90 px-4 py-3 text-[#18222f] shadow-[inset_0_1px_3px_rgba(0,0,0,0.07)] outline-none transition duration-200 placeholder:text-[#8090a7] focus:border-[#0f6a78] focus:ring-4 focus:ring-[#0f6a78]/20"
            rows={5}
            placeholder="Create a simple todo app with due dates and local storage"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-[#455a74]">
              Backend: <span className="font-mono text-xs">{API_BASE_URL}</span>
            </p>
            <button
              onClick={generateProject}
              disabled={loading}
              className="rounded-xl bg-gradient-to-r from-[#12253f] to-[#0f6a78] px-5 py-3 text-sm font-semibold text-[#f8f5ef] shadow-[0_10px_24px_rgba(15,106,120,0.28)] transition duration-200 hover:translate-y-[-1px] hover:from-[#0f6a78] hover:to-[#11868f] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Generating..." : "Generate App"}
            </button>
          </div>

          {wasCached && (
            <div className="mt-3 inline-flex items-center rounded-lg border border-[#9dd4bf] bg-[#ebfaf3] px-3 py-1.5 text-xs font-semibold text-[#176647]">
              Cache hit: served via optimized path.
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl border border-[#f1b0ab] bg-[#fff1ef] px-4 py-3 text-sm text-[#b73327]">
              {error}
            </div>
          )}

          {warning && (
            <div className="mt-4 rounded-xl border border-[#ecd39a] bg-[#fff8e8] px-4 py-3 text-sm text-[#b77a12]">
              {warning}
            </div>
          )}

          {appUrl && (
            <div className="mt-5 rounded-2xl border border-[#9dd4bf] bg-gradient-to-r from-[#ebfaf3] to-[#f1fbff] p-4">
              <p className="mb-3 text-sm font-medium text-[#1f9f68]">
                App generated successfully. Launch your preview:
              </p>
              <button
                onClick={runApp}
                className="rounded-xl bg-gradient-to-r from-[#1f9f68] to-[#1090a0] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(16,144,160,0.25)] transition duration-200 hover:translate-y-[-1px] hover:from-[#188a59] hover:to-[#0d7f8d]"
              >
                Run App
              </button>
            </div>
          )}
        </section>

        <div className="fade-in-up-late mt-10 text-center text-sm font-medium text-[#455a74]">
          User Prompt -&gt; AI Multi-Agent System -&gt; Generated Web App -&gt; Preview ;
        </div>
      </div>
    </main>
  );
}
