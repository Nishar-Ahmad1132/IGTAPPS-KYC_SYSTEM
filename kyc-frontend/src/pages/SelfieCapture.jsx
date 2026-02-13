import Webcam from "react-webcam";
import { useRef, useState } from "react";
import api from "../services/api";
import { useKycStore } from "../app/store";
import { useNavigate } from "react-router-dom";

export default function SelfieCapture() {
  const webcamRef = useRef(null);
  const user = useKycStore((s) => s.user);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const capture = async () => {
    if (!user?.user_id) {
      alert("User not found");
      return;
    }

    setLoading(true);

    const imageSrc = webcamRef.current.getScreenshot();
    const blob = await fetch(imageSrc).then((r) => r.blob());

    const formData = new FormData();
    formData.append("selfie", blob, "selfie.jpg");

    try {
      await api.post(`/selfie/capture/${user.user_id}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      navigate("/liveness");
    } catch (err) {
      console.error(err);
      alert("Selfie capture failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-lg backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-8 text-center">

        {/* Step Indicator */}
        <div className="mb-6 text-left">
          <p className="text-sm text-slate-400">Step 4 of 5</p>
          <div className="w-full h-2 bg-slate-700 rounded-full mt-2">
            <div className="w-4/5 h-2 bg-blue-500 rounded-full"></div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-white mb-2">
          Biometric Selfie Verification
        </h2>

        <p className="text-slate-400 text-sm mb-6">
          Position your face inside the frame and ensure good lighting.
        </p>

        {/* Webcam Container */}
        <div className="relative mx-auto w-full max-w-sm rounded-xl overflow-hidden border border-slate-700">
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            className="w-full"
            videoConstraints={{
              facingMode: "user",
            }}
          />

          {/* Face guide overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-56 h-56 border-4 border-white/40 rounded-full"></div>
          </div>
        </div>

        {/* Security Notice */}
        <div className="mt-4 text-xs text-slate-400">
          🔒 Your biometric data is securely processed and encrypted.
        </div>

        {/* Button */}
        <button
          disabled={loading}
          onClick={capture}
          className="mt-6 w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-medium text-white disabled:opacity-50"
        >
          {loading ? "Verifying Identity..." : "Capture & Continue"}
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
