import Webcam from "react-webcam";
import { useRef, useState } from "react";
import api from "../services/api";
import { useKycStore } from "../app/store";
import { useNavigate } from "react-router-dom";

const steps = [
  { action: "blink", text: "Please Blink Your Eyes" },
  { action: "left", text: "Turn Your Head LEFT" },
  { action: "right", text: "Turn Your Head RIGHT" },
];

export default function LivenessCheck() {
  const webcamRef = useRef(null);
  const user = useKycStore((s) => s.user);
  const setSimilarity = useKycStore((s) => s.setSimilarity);
  const navigate = useNavigate();

  const [stepIndex, setStepIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const captureFrames = async () => {
    const formData = new FormData();

    for (let i = 0; i < 6; i++) {
      await new Promise((r) => setTimeout(r, 400));

      const imageSrc = webcamRef.current?.getScreenshot();
      if (!imageSrc) continue;

      const blob = await fetch(imageSrc).then((r) => r.blob());
      formData.append("frames", blob, `frame_${i}.jpg`);
    }

    return formData;
  };

  const runStep = async () => {
    if (!user?.user_id) {
      setError("User not found");
      return;
    }

    if (!webcamRef.current) {
      setError("Camera not ready");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const current = steps[stepIndex];
      const formData = await captureFrames();

      const res = await api.post(
        `/liveness/step/${user.user_id}?action=${current.action}`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      if (!res.data.success) {
        setError("Action not detected. Please try again.");
        setLoading(false);
        return;
      }

      if (stepIndex < steps.length - 1) {
        setStepIndex((prev) => prev + 1);
        setLoading(false);
      } else {
        await completeFaceMatch();
      }
    } catch (err) {
      console.error(err);
      setError("Liveness verification failed.");
      setLoading(false);
    }
  };

  const completeFaceMatch = async () => {
    try {
      const res = await api.post(`/kyc/face-match/${user.user_id}`);

      setSimilarity({
        score: res.data.similarity,
        match: res.data.match,
      });

      navigate("/verification");
    } catch (err) {
      console.error(err);
      setError("Face matching failed.");
    } finally {
      setLoading(false);
    }
  };

  const progressPercent = ((stepIndex + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-lg backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-8 text-center relative">

        {/* Step Progress */}
        <div className="mb-6 text-left">
          <p className="text-sm text-slate-400">
            Step {stepIndex + 1} of {steps.length}
          </p>
          <div className="w-full h-2 bg-slate-700 rounded-full mt-2">
            <div
              className="h-2 bg-green-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-white mb-3">
          Liveness Verification
        </h2>

        <p className="text-slate-400 text-sm mb-6">
          {steps[stepIndex].text}
        </p>

        {/* Webcam Container */}
        <div className="relative mx-auto w-full max-w-sm rounded-xl overflow-hidden border border-slate-700">
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            audio={false}
            mirrored={true}
            videoConstraints={{ facingMode: "user" }}
            className="w-full"
          />

          {/* Circular Face Guide */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-56 h-56 border-4 border-white/40 rounded-full"></div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Button */}
        <button
          onClick={runStep}
          disabled={loading}
          className="mt-6 w-full py-3 rounded-lg bg-green-600 hover:bg-green-700 transition font-medium text-white disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Verify Action"}
        </button>

        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center rounded-2xl">
            <div className="text-white text-lg font-medium animate-pulse">
              Processing biometric data...
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
