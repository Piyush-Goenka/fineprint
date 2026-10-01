"use client";

import { useState } from "react";

const CMD = "python -m fineprint.market_data";

const CopyIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

const CheckIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

export function HeroCli() {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(CMD);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable — text is still selectable */
    }
  };

  return (
    <div className="fp-hero-cli-wrap">
      <div className="fp-hero-cli-row">
        <div className="fp-hero-cli">
          <span className="fp-hero-cli-prompt" aria-hidden>
            $
          </span>
          <code className="fp-hero-cli-cmd">
            python -m fineprint.market_data
          </code>
        </div>
        <button
          type="button"
          onClick={copy}
          className="fp-hero-cli-copy"
          aria-label={copied ? "Copied command" : "Copy refresh command"}
          title="Copy the local ranking refresh command"
        >
          {copied ? <CheckIcon /> : <CopyIcon />}
        </button>
      </div>
      <p className="fp-hero-cli-note">
        Refresh Flexprice Model Intelligence locally from public model rankings.{" "}
        <a href="https://github.com/flexprice/fineprint" target="_blank" rel="noopener noreferrer">Open source on GitHub</a>
        .
      </p>
    </div>
  );
}
