import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Compare models",
  description: "Compare model capability, preference, adoption, and Flexprice Index.",
};

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ models?: string }>;
}) {
  return (
    <div className="shell py-12">
      <p className="eyebrow mb-2">Compare</p>
      <h1 className="display text-[clamp(1.8rem,4.5vw,2.6rem)]">Compare model performance at a glance.</h1>
      <p className="mt-3 text-[15.5px] leading-relaxed text-muted max-w-[62ch]">Flexprice Model Intelligence brings capability, preference, and adoption into a consistent view, so you can compare models and choose one to try on contract extraction.</p>
      <div className="mt-7 grid sm:grid-cols-3 gap-3">{[["Capability", "A relative view of a model’s general problem-solving strength."], ["Preference", "How people rate model responses in direct comparisons."], ["Adoption", "A view of model usage over the recent period."]].map(([name, description], i) => <div key={name} className="panel rounded-xl p-5"><p className="eyebrow">{String(i + 1).padStart(2, "0")}</p><h2 className="mt-2 text-lg font-medium">{name}</h2><p className="mt-2 text-[13px] text-muted">{description}</p></div>)}</div>
      <Link href="/#leaderboard" className="btn btn-primary mt-7 inline-flex">Compare all models</Link>
    </div>
  );
}
