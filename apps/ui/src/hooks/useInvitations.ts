import { useCallback, useEffect, useState } from "react";
import { 
  InvitationSummary, 
  createInvitation as apiCreateInvitation, 
  listInvitations as apiListInvitations,
  revokeInvitation as apiRevokeInvitation,
  resendInvitation as apiResendInvitation
} from "../lib/api";

export const useInvitations = () => {
  const [invites, setInvites] = useState<InvitationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiListInvitations();
      setInvites(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load invitations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load().catch(() => undefined);
  }, [load]);

  const createInvitation = useCallback(async (email: string) => {
    try {
      const created = await apiCreateInvitation(email);
      setInvites((prev) => [created, ...prev]);
      return created;
    } catch (err: any) {
      setError(err?.message || "Failed to create invitation");
      throw err;
    }
  }, []);

  const revokeInvitation = useCallback(async (inviteId: string) => {
    try {
      await apiRevokeInvitation(inviteId);
      setInvites((prev) => prev.filter((i) => i.invite_id !== inviteId));
    } catch (err: any) {
      setError(err?.message || "Failed to revoke invitation");
      throw err;
    }
  }, []);

  const resendInvitation = useCallback(async (inviteId: string) => {
    try {
      await apiResendInvitation(inviteId);
    } catch (err: any) {
      setError(err?.message || "Failed to resend invitation");
      throw err;
    }
  }, []);

  return { invites, loading, error, reload: load, createInvitation, revokeInvitation, resendInvitation };
};
