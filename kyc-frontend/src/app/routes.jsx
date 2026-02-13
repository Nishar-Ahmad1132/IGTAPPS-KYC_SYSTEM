import { Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";

import Register from "../pages/Register";
import AadhaarUpload from "../pages/AadhaarUpload";
import OCRReview from "../pages/OCRReview";
import SelfieCapture from "../pages/SelfieCapture";
import LivenessCheck from "../pages/LivenessCheck";
import VerificationResult from "../pages/VerificationResult";
import Dashboard from "../pages/Dashboard";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Register />} />
        <Route path="/aadhaar" element={<AadhaarUpload />} />
        <Route path="/ocr-review" element={<OCRReview />} />
        <Route path="/selfie" element={<SelfieCapture />} />
        <Route path="/liveness" element={<LivenessCheck />} />
        <Route path="/verification" element={<VerificationResult />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>
    </Routes>
  );
}
