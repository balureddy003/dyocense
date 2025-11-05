import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../lib/config";

interface InviteDetails {
  tenant_id: string;
  tenant_name: string;
  invitee_email: string;
  message: string;
}

export const AcceptInvitePage = () => {
  const { inviteId } = useParams<{ inviteId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [details, setDetails] = useState<InviteDetails | null>(null);

  useEffect(() => {
    if (!inviteId) {
      setError("Invalid invitation link");
      setLoading(false);
      return;
    }

    const acceptInvite = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/v1/invitations/${inviteId}/accept`, {
          method: "POST",
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Invitation not found or expired");
          }
          throw new Error("Failed to accept invitation");
        }

        const data: InviteDetails = await response.json();
        setDetails(data);
      } catch (err: any) {
        setError(err.message || "Failed to accept invitation");
      } finally {
        setLoading(false);
      }
    };

    acceptInvite();
  }, [inviteId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="mt-4 text-sm text-gray-600">Accepting invitation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="max-w-md w-full mx-4 rounded-2xl border border-red-200 bg-white shadow-lg px-8 py-10 text-center">
          <div className="text-red-500 text-5xl mb-4">✕</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invitation Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-md w-full mx-4 rounded-2xl border border-green-200 bg-white shadow-lg px-8 py-10 text-center">
        <div className="text-green-500 text-5xl mb-4">✓</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Invitation Accepted!</h1>
        <p className="text-gray-600 mb-6">{details?.message}</p>
        <div className="bg-blue-50 rounded-lg px-4 py-3 mb-6 text-sm text-left">
          <p className="font-semibold text-gray-900">Organization: {details?.tenant_name}</p>
          <p className="text-gray-600">Email: {details?.invitee_email}</p>
          <p className="text-gray-600">Tenant ID: {details?.tenant_id}</p>
        </div>
        <button
          onClick={() => navigate(`/login?tenant=${details?.tenant_id}&email=${details?.invitee_email}`)}
          className="w-full px-6 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-blue-700 mb-3"
        >
          Go to Login
        </button>
        <button
          onClick={() => navigate("/")}
          className="w-full px-6 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300"
        >
          Go to Home
        </button>
      </div>
    </div>
  );
};
