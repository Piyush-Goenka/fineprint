import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { marketData, marketDataUpdatedDate } from "@/lib/market-data";
import { ProviderIcon } from "@/components/provider-icon";

export function generateStaticParams() {
  return marketData.rows.map((model) => ({ id: model.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const model = marketData.rows.find((row) => row.id === decodeURIComponent(id));
  if (!model) return {};
  return { title: `${model.label} · Flexprice Model Intelligence`, description: `${model.label} capability, preference, adoption, and Flexprice Index.` };
}

export default async function ModelPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const model = marketData.rows.find((row) => row.id === decodeURIComponent(id));
  if (!model) notFound();
  return <div className="shell py-12">
    <Link href="/#leaderboard" className="font-mono text-[12px] text-faint hover:text-muted">Back to rankings</Link>
    <div className="mt-4 flex items-center gap-3"><ProviderIcon brand={model.creator} size={30} /><h1 className="display text-[clamp(2rem,5vw,2.8rem)]">{model.label}</h1></div>
    <p className="mt-3 text-muted">Flexprice model metrics · updated {marketDataUpdatedDate}.</p>
    <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{[
      ["Capability", "capability", model.metrics?.capability], ["Preference", "preference", model.metrics?.preference],
      ["Adoption", "adoption", model.metrics?.adoption], ["Flexprice Index", "overall", model.overall],
    ].map(([label, key, value]) => {
      const description = key === "overall" ? "Weighted score across all three metrics" : key === "capability" ? "Benchmark and model features" : key === "preference" ? "Developer selection and Arena" : "Monthly model usage";
      return <section key={String(label)} className="card rounded-xl p-5"><p className="font-mono text-[11px] uppercase tracking-[.1em] text-faint">{label}</p><p className="mt-2 text-3xl font-semibold">{value == null ? "—" : Number(value).toFixed(1)}</p><p className="mt-1 text-[12px] text-muted">{description}</p></section>;
    })}</div>
    <p className="mt-8 text-[12px] text-muted">The Index follows one scoring formula for every model. These values describe the broader model landscape, not FinePrint contract-extraction accuracy. Read the <Link href="/methodology" className="text-accent hover:underline">methodology</Link>.</p>
  </div>;
}
