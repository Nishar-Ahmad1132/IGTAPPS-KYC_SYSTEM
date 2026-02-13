import { useEffect, useState } from "react";
import { useKycStore } from "../app/store";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function VerificationResult() {
  const user = useKycStore((s) => s.user);
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [finalStatus, setFinalStatus] = useState(null);

  useEffect(() => {
    if (!user?.user_id) return;

    const runFinalDecision = async () => {
      try {
        const res = await api.post(
          `/kyc/final-decision/${user.user_id}`
        );
        setFinalStatus(res.data.final_status);
      } catch (err) {
        console.error("Final decision error:", err);
        setFinalStatus("FAILED");
      } finally {
        setLoading(false);
      }
    };

    runFinalDecision();
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-10 text-center shadow-2xl">
          <div className="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-6"></div>
          <p className="text-lg font-medium text-white">
            Processing Final KYC Decision...
          </p>
          <p className="text-sm text-slate-400 mt-2">
            Please wait while we verify your identity.
          </p>
        </div>
      </div>
    );
  }

  const isVerified = finalStatus === "VERIFIED";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-md backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-10 text-center">

        {/* Icon */}
        <div
          className={`mx-auto mb-6 flex items-center justify-center h-20 w-20 rounded-full ${
            isVerified
              ? "bg-green-500/20 border border-green-500/40"
              : "bg-red-500/20 border border-red-500/40"
          }`}
        >
          <span className="text-4xl">
            {isVerified ? "✓" : "✕"}
          </span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-semibold text-white mb-3">
          Final KYC Result
        </h2>

        {/* Status */}
        <p
          className={`text-xl font-bold mb-4 ${
            isVerified ? "text-green-400" : "text-red-400"
          }`}
        >
          {finalStatus}
        </p>

        {/* Message */}
        <p className="text-slate-400 text-sm mb-8">
          {isVerified
            ? "Your identity has been successfully verified. You now have full access."
            : "Verification failed. Please retry the KYC process or contact support."}
        </p>

        {/* Button */}
        <button
          onClick={() => navigate("/dashboard")}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-medium text-white"
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  );
}
