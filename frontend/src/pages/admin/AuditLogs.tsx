import { RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { adminApi, type AdminAuditLog } from '@/services/admin';
import { usePageTitle } from '@/hooks/usePageTitle';

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function AuditLogs() {
  const [logs, setLogs] = useState<AdminAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  usePageTitle('VisionPass AI | Audit Logs');

  async function loadLogs() {
    try {
      setError('');
      setRefreshing(true);
      const response = await adminApi.listAuditLogs();
      setLogs(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load audit logs.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadLogs();
  }, []);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Audit trail</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Audit logs</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Track super-admin activity, entity changes, and sensitive platform events in one place.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadLogs()} disabled={refreshing}>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Latest events</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">User, action, entity, and timestamp.</p>
            </div>
            <Badge tone="neutral">{logs.length} entries</Badge>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-white/10">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-950/40 dark:text-slate-400">
              <tr>
                <th className="px-5 py-4 font-medium">User</th>
                <th className="px-5 py-4 font-medium">Action</th>
                <th className="px-5 py-4 font-medium">Entity</th>
                <th className="px-5 py-4 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white dark:divide-white/10 dark:bg-slate-950/40">
              {loading ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={4}>Loading audit logs...</td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={4}>No audit logs yet.</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-5 py-4 align-top font-medium text-slate-900 dark:text-white">{log.user}</td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{log.action}</td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{log.entity}</td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{formatTimestamp(log.timestamp)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
