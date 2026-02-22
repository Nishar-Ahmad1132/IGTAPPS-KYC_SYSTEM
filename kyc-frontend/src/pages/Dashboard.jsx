import { useEffect, useState } from "react";
import api from "../services/api";
import { useKycStore } from "../app/store";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const user = useKycStore((s) => s.user);
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!user?.user_id) return;

    const fetchData = async () => {
      try {
        const userRes = await api.get(`/users/${user.user_id}`);
        setProfile(userRes.data);

        const statusRes = await api.get(`/kyc/status/${user.user_id}`);
        setStatus(statusRes.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
  }, [user]);

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
        <div className="text-white text-lg animate-pulse">
          Loading dashboard...
        </div>
      </div>
    );
  }

  // -------------------------------------------
  // 1. Define Logic for all States
  // -------------------------------------------
  const kycStatus = status?.kyc_status || "PENDING";

  const isVerified = kycStatus === "VERIFIED";
  const isFailed = kycStatus.includes("FAILED");
  const isManualReview = kycStatus === "MANUAL_REVIEW";

  // -------------------------------------------
  // 2. Dynamic Styling & Messages
  // -------------------------------------------
  let statusColor = "bg-blue-500/20 text-blue-400 border-blue-500/40"; // Default Pending
  let statusMessage = "Please complete your KYC process.";

  if (isVerified) {
    statusColor = "bg-green-500/20 text-green-400 border-green-500/40";
    statusMessage = "You are fully verified! You can now access all features.";
  } else if (isFailed) {
    statusColor = "bg-red-500/20 text-red-400 border-red-500/40";
    statusMessage =
      "Verification failed. Please retry the process with clear documents.";
  } else if (isManualReview) {
    statusColor = "bg-orange-500/20 text-orange-400 border-orange-500/40";
    statusMessage =
      "Your ID photo appears older than your selfie. We have sent your application for Manual Review. This usually takes 24-48 hours.";
  } else {
    // Pending / Basic Submitted
    statusColor = "bg-yellow-500/20 text-yellow-400 border-yellow-500/40";
    statusMessage = "Your verification is currently in progress.";
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4 py-10">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-white">KYC Dashboard</h1>
          <div className="text-sm text-slate-400">Welcome back 👋</div>
        </div>

        {/* Profile Card */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-white mb-4">
            Profile Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300 text-sm">
            <div>
              <p className="text-slate-400">Full Name</p>
              <p className="text-white font-medium">
                {profile.first_name} {profile.last_name}
              </p>
            </div>

            <div>
              <p className="text-slate-400">Pan Number</p>
              <p className="text-white font-medium">
                {profile.pan_number || "Not provided"}
              </p>
            </div>

            <div>
              <p className="text-slate-400">Email</p>
              <p className="text-white font-medium">{profile.email}</p>
            </div>

            <div>
              <p className="text-slate-400">Mobile</p>
              <p className="text-white font-medium">{profile.mobile}</p>
            </div>

            <div>
              <p className="text-slate-400">User ID</p>
              <p className="text-white font-medium">#{profile.id}</p>
            </div>
          </div>
        </div>

        {/* KYC Status Card */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl text-center">
          <h2 className="text-lg font-semibold text-white mb-4">
            Current KYC Status
          </h2>

          {/* Status Badge */}
          <div
            className={`inline-block px-6 py-3 rounded-full border font-bold tracking-wide ${statusColor}`}
          >
            {kycStatus.replace("_", " ")}
          </div>

          {/* Helper Text */}
          <p className="text-slate-300 text-sm mt-6 max-w-lg mx-auto leading-relaxed">
            {statusMessage}
          </p>

          {/* Action Buttons */}
          {isFailed && (
            <button
              onClick={() => navigate("/aadhaar")}
              className="mt-6 px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-medium text-white shadow-lg shadow-blue-500/20"
            >
              Retry KYC
            </button>
          )}

          {/* Manual Review Specific UI - No Retry Button, just Wait */}
          {isManualReview && (
            <div className="mt-6 text-xs text-slate-500 uppercase tracking-widest">
              Action Required: None (Please Wait)
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
