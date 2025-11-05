import { useMemo, useState } from "react";
import { useInvitations } from "../hooks/useInvitations";

export const InviteTeammateCard = () => {
  const { invites, loading, error, createInvitation, reload, revokeInvitation, resendInvitation } = useInvitations();
  const [email, setEmail] = useState("");
  const [creating, setCreating] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [lastInviteId, setLastInviteId] = useState<string | null>(null);
  const [errMsg, setErrMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const pendingInvites = useMemo(() => invites.filter((i) => i.status !== "accepted"), [invites]);

  const onInvite = async () => {
    setErrMsg(null);
    setSuccessMsg(null);
    const trimmed = email.trim();
    if (!trimmed || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(trimmed)) {
      setErrMsg("Enter a valid email address");
      return;
    }
    setCreating(true);
    try {
      const created = await createInvitation(trimmed);
      setEmail("");
      setSuccessMsg(`Invitation sent to ${created.invitee_email}`);
      setLastInviteId(created.invite_id);
    } catch (e: any) {
      setErrMsg(e?.message || "Failed to send invitation");
    } finally {
      setCreating(false);
    }
  };

  const onRevoke = async (inviteId: string) => {
    setActionLoading(inviteId);
    setErrMsg(null);
    setSuccessMsg(null);
    try {
      await revokeInvitation(inviteId);
      setSuccessMsg("Invitation revoked");
    } catch (e: any) {
      setErrMsg(e?.message || "Failed to revoke invitation");
    } finally {
      setActionLoading(null);
    }
  };

  const onResend = async (inviteId: string) => {
    setActionLoading(inviteId);
    setErrMsg(null);
    setSuccessMsg(null);
    try {
      await resendInvitation(inviteId);
      setSuccessMsg("Invitation resent");
    } catch (e: any) {
      setErrMsg(e?.message || "Failed to resend invitation");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="rounded-2xl border border-gray-100 bg-white shadow-sm px-6 py-5 space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Team</p>
          <h2 className="text-sm font-semibold text-gray-900">Invite teammate</h2>
        </div>
      </header>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {errMsg && <p className="text-xs text-red-600">{errMsg}</p>}
      {successMsg && (
        <div className="text-xs text-emerald-700 space-y-1">
          <p>{successMsg}</p>
          {lastInviteId && (
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Accept link:</span>
              <a
                className="text-primary underline"
                href={`/accept-invite/${lastInviteId}`}
                target="_blank"
                rel="noreferrer"
              >
                /accept-invite/{lastInviteId}
              </a>
              <button
                onClick={() => navigator.clipboard.writeText(`${window.location.origin}/accept-invite/${lastInviteId}`)}
                className="px-2 py-1 rounded border border-gray-300 text-gray-700 hover:bg-gray-100"
              >
                Copy
              </button>
            </div>
          )}
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <input
          type="email"
          placeholder="teammate@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 min-w-[240px] px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button
          onClick={() => void onInvite()}
          disabled={creating}
          className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700"
        >
          {creating ? "Sending…" : "Send invite"}
        </button>
        <button
          onClick={() => void reload()}
          className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200"
        >
          Refresh
        </button>
      </div>
      <div className="space-y-2 text-xs text-gray-600">
        {loading ? (
          <p>Loading invitations…</p>
        ) : pendingInvites.length ? (
          pendingInvites.map((i) => (
            <div key={i.invite_id} className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 bg-gray-50">
              <div>
                <p className="font-medium text-gray-800">{i.invitee_email}</p>
                <p className="text-gray-500">
                  Expires {new Date(i.expires_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500 uppercase text-[10px] font-semibold">{i.status}</span>
                {i.status === "pending" && (
                  <>
                    <button
                      onClick={() => void onResend(i.invite_id)}
                      disabled={actionLoading === i.invite_id}
                      className="px-2 py-1 rounded text-[10px] font-semibold uppercase bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50"
                    >
                      {actionLoading === i.invite_id ? "..." : "Resend"}
                    </button>
                    <button
                      onClick={() => void onRevoke(i.invite_id)}
                      disabled={actionLoading === i.invite_id}
                      className="px-2 py-1 rounded text-[10px] font-semibold uppercase bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
                    >
                      {actionLoading === i.invite_id ? "..." : "Revoke"}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        ) : (
          <p>No pending invitations</p>
        )}
      </div>
    </div>
  );
};
