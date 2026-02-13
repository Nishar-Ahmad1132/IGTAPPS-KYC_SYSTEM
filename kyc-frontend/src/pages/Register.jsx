import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { useState } from "react";
import { useKycStore } from "../app/store";
import api from "../services/api";

const schema = z.object({
  first_name: z.string().min(2, "First name must be at least 2 characters"),
  last_name: z.string().min(2, "Last name must be at least 2 characters"),
  email: z.string().email("Enter a valid email"),
  mobile: z.string().regex(/^\d{10}$/, "Mobile must be 10 digits"),
  pan_number: z.string().regex(
    /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
    "Invalid PAN format (ABCDE1234F)"
  ),
});

export default function Register() {
  const navigate = useNavigate();
  const setUser = useKycStore((s) => s.setUser);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (data) => {
    setLoading(true);

    try {
      const res = await api.post("/users/register", data);
      setUser(res.data);
      navigate("/aadhaar");
    } catch (err) {
      if (err.response?.data?.detail?.toLowerCase().includes("exist")) {
        try {
          const loginRes = await api.post("/users/login", {
            email: data.email,
            mobile: data.mobile,
          });

          setUser(loginRes.data);
          navigate("/aadhaar");
        } catch {
          alert("User exists but login failed");
        }
      } else {
        alert(err.response?.data?.detail || "Registration failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 px-4">
      <div className="w-full max-w-md backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-8">

        {/* Step Indicator */}
        <div className="mb-6">
          <p className="text-sm text-slate-400">Step 1 of 5</p>
          <div className="w-full h-2 bg-slate-700 rounded-full mt-2">
            <div className="w-1/5 h-2 bg-blue-500 rounded-full"></div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold text-white mb-6">
          Basic Information
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

          {/* First Name */}
          <div>
            <input
              {...register("first_name")}
              placeholder="First Name"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white outline-none transition"
            />
            {errors.first_name && (
              <p className="text-red-400 text-sm mt-1">
                {errors.first_name.message}
              </p>
            )}
          </div>

          {/* Last Name */}
          <div>
            <input
              {...register("last_name")}
              placeholder="Last Name"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white outline-none transition"
            />
            {errors.last_name && (
              <p className="text-red-400 text-sm mt-1">
                {errors.last_name.message}
              </p>
            )}
          </div>

          {/* Email */}
          <div>
            <input
              {...register("email")}
              placeholder="Email Address"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white outline-none transition"
            />
            {errors.email && (
              <p className="text-red-400 text-sm mt-1">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Mobile */}
          <div>
            <input
              {...register("mobile")}
              placeholder="Mobile Number"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white outline-none transition"
            />
            {errors.mobile && (
              <p className="text-red-400 text-sm mt-1">
                {errors.mobile.message}
              </p>
            )}
          </div>

          {/* PAN */}
          <div>
            <input
              {...register("pan_number")}
              placeholder="PAN Number"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white outline-none transition uppercase"
            />
            {errors.pan_number && (
              <p className="text-red-400 text-sm mt-1">
                {errors.pan_number.message}
              </p>
            )}
          </div>

          {/* Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition font-medium text-white disabled:opacity-50"
          >
            {loading ? "Processing..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
