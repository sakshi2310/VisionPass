import { Plus, PencilLine, Eye, Save } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useApp } from "@/context/AppContext";
import type { RuleStatus } from "@/types";

const emptyRuleDraft = {
  name: "",
  description: "",
  category: "Object detection",
  tenantScope: "All tenants",
  status: "draft" as RuleStatus,
  enabled: true,
  threshold: 80,
  action: "Create alert and notify security",
};

export function Rules() {
  const { featureRules, createRule, updateRule } = useApp();
  const [selectedRuleId, setSelectedRuleId] = useState(featureRules[0]?.id ?? "");
  const [draft, setDraft] = useState({ ...emptyRuleDraft });

  const selectedRule = useMemo(
    () => featureRules.find((rule) => rule.id === selectedRuleId) ?? null,
    [featureRules, selectedRuleId],
  );

  useEffect(() => {
    if (selectedRule) {
      setDraft({
        name: selectedRule.name,
        description: selectedRule.description,
        category: selectedRule.category,
        tenantScope: selectedRule.tenantScope,
        status: selectedRule.status,
        enabled: selectedRule.enabled,
        threshold: selectedRule.threshold,
        action: selectedRule.action,
      });
    }
  }, [selectedRule]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (selectedRule) {
      updateRule(selectedRule.id, draft);
    } else {
      const created = createRule(draft);
      setSelectedRuleId(created.id);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Feature rules</p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
              Create, view, and modify feature rules
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              Add new logic like object detection, after-hours alerts, or access anomalies, then fine-tune the rule
              without leaving the super-admin console.
            </p>
          </div>
          <Button
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => {
              setSelectedRuleId("");
              setDraft({ ...emptyRuleDraft });
            }}
          >
            New rule
          </Button>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="grid gap-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Rule library</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Select a rule to view or edit it.</p>
          </div>

          <div className="grid gap-3">
            {featureRules.map((rule) => (
              <button
                key={rule.id}
                type="button"
                onClick={() => setSelectedRuleId(rule.id)}
                className={`rounded-2xl border p-4 text-left transition ${
                  selectedRuleId === rule.id
                    ? "border-brand-500/30 bg-brand-500/5"
                    : "border-slate-200 bg-white hover:border-slate-300 dark:border-white/10 dark:bg-white/5"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="font-medium text-slate-900 dark:text-white">{rule.name}</div>
                      <Badge tone={rule.status === "active" ? "success" : rule.status === "paused" ? "warning" : "neutral"}>
                        {rule.status}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">{rule.description}</p>
                  </div>
                  <Eye className="h-4 w-4 text-slate-400" />
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span>{rule.category}</span>
                  <span>-</span>
                  <span>{rule.tenantScope}</span>
                  <span>-</span>
                  <span>{rule.threshold}% threshold</span>
                </div>
              </button>
            ))}
          </div>
        </Card>

        <Card className="grid gap-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                {selectedRule ? "Edit rule" : "Create a new rule"}
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Build a rule for object detection, movement anomalies, or any future module.
              </p>
            </div>
            {selectedRule ? (
              <Badge tone={selectedRule.enabled ? "success" : "neutral"}>
                {selectedRule.enabled ? "enabled" : "disabled"}
              </Badge>
            ) : null}
          </div>

          <form onSubmit={handleSubmit} className="grid gap-4">
            <Input
              label="Rule name"
              value={draft.name}
              onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
              placeholder="Object detection review"
            />
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Description</span>
              <textarea
                value={draft.description}
                onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
                rows={4}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-white"
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Category"
                value={draft.category}
                onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))}
                placeholder="Object detection"
              />
              <Input
                label="Tenant scope"
                value={draft.tenantScope}
                onChange={(event) => setDraft((current) => ({ ...current, tenantScope: event.target.value }))}
                placeholder="All tenants"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Status</span>
                <select
                  value={draft.status}
                  onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as RuleStatus }))}
                  className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                </select>
              </label>

              <Input
                label="Threshold"
                type="number"
                min="0"
                max="100"
                value={draft.threshold}
                onChange={(event) => setDraft((current) => ({ ...current, threshold: Number(event.target.value) }))}
              />
            </div>

            <Input
              label="Action"
              value={draft.action}
              onChange={(event) => setDraft((current) => ({ ...current, action: event.target.value }))}
              placeholder="Create alert and notify security"
            />

            <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Enabled</div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Turn the rule on for live processing.</p>
              </div>
              <input
                type="checkbox"
                checked={draft.enabled}
                onChange={(event) => setDraft((current) => ({ ...current, enabled: event.target.checked }))}
                className="h-5 w-5 accent-brand-600"
              />
            </label>

            <div className="flex flex-wrap gap-3">
              <Button
                type="submit"
                leftIcon={selectedRule ? <PencilLine className="h-4 w-4" /> : <Save className="h-4 w-4" />}
              >
                {selectedRule ? "Save changes" : "Create rule"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setSelectedRuleId("");
                  setDraft({ ...emptyRuleDraft });
                }}
              >
                Clear form
              </Button>
            </div>
          </form>
        </Card>
      </section>
    </div>
  );
}
