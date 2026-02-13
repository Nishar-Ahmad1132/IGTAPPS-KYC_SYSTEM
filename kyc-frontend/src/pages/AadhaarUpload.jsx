import { useState } from "react";
import api from "../services/api";
import { useNavigate } from "react-router-dom";
import { useKycStore } from "../app/store";

export default function AadhaarUpload() {
  const [front, setFront] = useState(null);
  const [back, setBack] = useState(null);
  const [loading, setLoading] = useState(false);

  const user = useKycStore((s) => s.user);
  const setOcrData = useKycStore((s) => s.setOcrData);
  const navigate = useNavigate();

  const upload = async () => {
    if (!front || !back) {
      alert("Please upload both images");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("front", front);
    formData.append("back", back);

    try {
      const res = await api.post(
        `/upload/aadhaar/${user.user_id}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setOcrData(res.data.ocr_result);
      navigate("/ocr-review");
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-lg backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-8">

        {/* Step Indicator */}
        <div className="mb-6">
          <p className="text-sm text-slate-400">Step 2 of 5</p>
          <div className="w-full h-2 bg-slate-700 rounded-full mt-2">
            <div className="w-2/5 h-2 bg-blue-500 rounded-full"></div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-white mb-6">
          Upload Aadhaar Document
        </h2>

        <div className="space-y-5">

          {/* Front Upload */}
          <label className="block">
            <div className="border-2 border-dashed border-slate-600 rounded-xl p-6 text-center cursor-pointer hover:border-blue-500 transition">
              <p className="text-slate-400 text-sm mb-2">
                Upload Aadhaar Front
              </p>
              <p className="text-white font-medium">
                {front ? front.name : "Click to select image"}
              </p>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => setFront(e.target.files[0])}
              />
            </div>
          </label>

          {/* Back Upload */}
          <label className="block">
            <div className="border-2 border-dashed border-slate-600 rounded-xl p-6 text-center cursor-pointer hover:border-blue-500 transition">
              <p className="text-slate-400 text-sm mb-2">
                Upload Aadhaar Back
              </p>
              <p className="text-white font-medium">
                {back ? back.name : "Click to select image"}
              </p>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => setBack(e.target.files[0])}
              />
            </div>
          </label>

          {/* Security Note */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm text-slate-400">
            🔒 Your documents are securely encrypted and stored.
          </div>

          {/* Upload Button */}
          <button
            onClick={upload}
            disabled={loading}
            className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-medium text-white disabled:opacity-50"
          >
            {loading ? "Processing OCR..." : "Upload & Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
