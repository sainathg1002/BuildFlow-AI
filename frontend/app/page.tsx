"use client";

import { useState } from "react";
import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://buildflow-ai.onrender.com";

type GenerateResponse = {
  app_url?: string;
  project?: string;
  error?: string;
  warning?: string;
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

  const generateProject = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setError("");
    setWarning("");
    setAppUrl("");

    try {
      const response = await axios.post<GenerateResponse>(
        `${API_BASE_URL}/generate`,
        {
          prompt,
          recursion_limit: 12,
        }
      );

      const data = response.data;
      if (data.error) {
        setError(data.error);
        return;
      }

      if (!data.app_url) {
        setError("Generation completed, but no runnable app URL was returned.");
        return;
      }

      setAppUrl(toAbsoluteUrl(data.app_url));
      if (data.warning) {
        setWarning(data.warning);
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const apiError = err.response?.data?.detail ?? err.response?.data?.error;
        setError(apiError || "Failed to generate project.");
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
    <main className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-2xl">
        <h1 className="text-3xl font-bold text-center mb-4">BuildFlow AI</h1>

        <textarea
          className="w-full border p-3 rounded-lg mb-4"
          rows={4}
          placeholder="Create a simple todo app"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />

        <button
          onClick={generateProject}
          disabled={loading}
          className="w-full bg-black text-white py-3 rounded-lg hover:bg-gray-800 disabled:opacity-60"
        >
          {loading ? "Generating..." : "Generate App"}
        </button>

        {error && <p className="text-red-500 mt-4 text-center">{error}</p>}

        {warning && (
          <p className="text-amber-600 mt-4 text-center">{warning}</p>
        )}

        {appUrl && (
          <div className="mt-6 flex flex-col gap-3">
            <button
              onClick={runApp}
              className="bg-green-600 text-white py-2 rounded-lg"
            >
              Run App
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
