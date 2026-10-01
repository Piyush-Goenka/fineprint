import Link from "next/link";
import Image from "next/image";
import { Leaderboard } from "@/components/leaderboard";
import { Playground } from "@/components/playground";
import { WhatsInside } from "@/components/whats-inside";
import { ProblemStatement } from "@/components/problem-statement";
import { TeamNote } from "@/components/team-note";
import { FlexpriceCta } from "@/components/flexprice-cta";
import { LabMarquee } from "@/components/lab-marquee";
import { HeroCli } from "@/components/hero-cli";
import { EmbedSnippet } from "@/components/embed-snippet";

const LinkArrow = () => (
  <svg viewBox="0 0 24 24" aria-hidden fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round"
    className="size-3.5 shrink-0 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
    <path d="M7 17 17 7M17 7H9M17 7v8" />
  </svg>
);

export default function Home() {

  return (
    <>
      <section className="relative isolate overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="fp-hero-art">
            <Image src="/hero/style-archive.webp" alt="A vivid vermilion temple archive of rolled contracts, a robed scholar reading a scroll of fine print cascading down the steps, in a lush orange garden under a cobalt sky"
              fill priority sizes="(max-width: 768px) 100vw, 72vw" className="object-cover fp-hero-art-img" style={{ objectPosition: "40% 48%" }} />
          </div>
          <div aria-hidden className="absolute inset-0 fp-hero-wash" />
          <div aria-hidden className="absolute inset-x-0 top-0 h-44"
            style={{ background: "linear-gradient(180deg, var(--bg) 0%, color-mix(in srgb, var(--bg) 45%, transparent) 58%, transparent 100%)" }} />
          <div aria-hidden className="absolute inset-x-0 bottom-0 h-36"
            style={{ background: "linear-gradient(0deg, var(--bg) 0%, transparent 100%)" }} />
        </div>

        <div className="shell flex flex-col min-h-0 md:min-h-[88vh] lg:min-h-[90vh] pt-16 md:pt-20 pb-10 md:pb-14">
          <div className="flex flex-1 flex-col justify-center">
            <h1 className="display text-[clamp(2.2rem,4.6vw,3.5rem)] max-w-[20ch] fp-up" style={{ animationDelay: ".07s" }}>
              Can your favorite model read the fine print?
            </h1>
            <p className="mt-5 sm:mt-7 text-[15.5px] sm:text-[19.5px] leading-[1.55] sm:leading-[1.62] max-w-[40ch] text-muted fp-up" style={{ animationDelay: ".12s" }}>
              Signed contracts bury their billing terms in pages of prose. Explore how models compare,
              then try contract extraction yourself.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 fp-up" style={{ animationDelay: ".15s" }}>
              <Link href="/compare" className="btn btn-primary btn-lg">Explore model signals</Link>
              <Link href="#leaderboard" className="btn px-0 py-3 border-0 bg-transparent text-muted hover:text-text transition-colors">
                See model rankings
              </Link>
            </div>
            <div className="fp-up" style={{ animationDelay: ".19s" }}>
              <HeroCli />
            </div>
          </div>

          <div className="shrink-0 pt-12 md:pt-20 lg:pt-24 w-full max-w-[min(100%,38rem)] md:max-w-[min(100%,42%)] fp-up" style={{ animationDelay: ".24s" }}>
            <p className="eyebrow mb-4">Model providers</p>
            <LabMarquee />
          </div>
        </div>
      </section>

      <ProblemStatement />

      <WhatsInside />

      <section id="leaderboard" className="shell py-10 sm:py-14">
        <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
          <div>
            <p className="eyebrow mb-3">Flexprice Model Intelligence</p>
            <h2 className="display text-[clamp(1.9rem,4.2vw,2.6rem)]">A clearer view of the model landscape.</h2>
          </div>
          <EmbedSnippet />
        </div>
        <div className="panel rounded-xl overflow-hidden"><Leaderboard /></div>
      </section>

      {/* Keep the contract scanning demo available alongside public model signals. */}
      <section id="try" className="shell py-12 sm:py-16">
        <p className="eyebrow mb-3">Try it</p>
        <h2 className="display text-[clamp(1.9rem,4.2vw,2.6rem)]">Read a contract with any model.</h2>
        <p className="mt-3 text-[14.5px] text-muted max-w-[58ch]">
          Try one of the top models live on our samples, or upload your own contract. We run
          extraction in real time (it can take a minute depending on the model) and show you
          every field it pulls out.
        </p>
        <div className="mt-8">
          <Playground />
        </div>
      </section>

      <section className="shell pt-10 pb-4"><p className="text-[12px] text-muted">Model metrics are refreshed regularly using a consistent scoring method.</p></section>

      <TeamNote />

      <FlexpriceCta />
    </>
  );
}
