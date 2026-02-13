import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useKycStore } from "../app/store";
import api from "../services/api";

export default function OCRReview() {
  // const ocrData = useKycStore((s) => s.ocrData);
  const { ocrData, setOcrData, user } = useKycStore();
  const navigate = useNavigate();
  const [showAadhaar, setShowAadhaar] = useState(false);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userId = user?.id || user?.user_id;

    if (!userId) return;

    const fetchOCR = async () => {
      try {
        const res = await api.get(`/kyc/ocr/${userId}`);
        setOcrData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchOCR();
  }, [user]);

  console.log("USER:", user);

  if (loading) {
    return <p className="text-white text-center">Loading...</p>;
  }

  if (!ocrData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
        <div className="max-w-md w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 text-center">
          <h2 className="text-xl font-semibold text-white mb-4">
            OCR Result Not Found
          </h2>
          <p className="text-slate-400 mb-6">
            Please upload your Aadhaar document again.
          </p>
          <button
            onClick={() => navigate("/aadhaar")}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg w-full text-white"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const fullAadhaar = ocrData.aadhaar_full;
  const maskedAadhaar = ocrData.aadhaar_number;

  const displayAadhaar = showAadhaar
    ? fullAadhaar
    : maskedAadhaar || "Not detected";

  const confidence = ocrData.confidence || ocrData.confidence_score || 0;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-lg backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-8">
        {/* Step Indicator */}
        <div className="mb-6">
          <p className="text-sm text-slate-400">Step 3 of 5</p>
          <div className="w-full h-2 bg-slate-700 rounded-full mt-2">
            <div className="w-3/5 h-2 bg-green-500 rounded-full"></div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-white mb-6">
          OCR Verification Result
        </h2>

        <div className="space-y-4">
          {/* Name */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-sm text-slate-400">Full Name</p>
            <p className="text-white font-medium">
              {ocrData.name || "Not detected"}
            </p>
          </div>

          {/* DOB */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-sm text-slate-400">Date of Birth</p>
            <p className="text-white font-medium">
              {ocrData.dob || "Not detected"}
            </p>
          </div>

          {/* Aadhaar */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-sm text-slate-400">Aadhaar Number</p>

            <div className="flex items-center justify-between mt-1">
              <p className="text-white font-medium">{displayAadhaar}</p>

              {fullAadhaar && (
                <button
                  onClick={() => setShowAadhaar(!showAadhaar)}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  {showAadhaar ? "Hide" : "Show"}
                </button>
              )}
            </div>
          </div>

          {/* Confidence */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-sm text-slate-400 mb-2">OCR Confidence</p>

            <div className="w-full bg-slate-700 h-2 rounded-full">
              <div
                className="h-2 rounded-full bg-green-500"
                style={{ width: `${confidence * 100}%` }}
              ></div>
            </div>

            <p className="text-right text-xs text-slate-400 mt-1">
              {confidence ? `${confidence * 100}%` : "N/A"}
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate("/selfie")}
          className="mt-6 w-full py-3 rounded-lg bg-green-600 hover:bg-green-700 transition font-medium text-white"
        >
          Continue to Selfie Verification
        </button>
      </div>
    </div>
  );
}
